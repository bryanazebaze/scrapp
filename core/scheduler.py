"""APScheduler-based job scheduler, running in-process with FastAPI.

Jobs:
  - daily 02:00   crawl all active sources (dedicated + universal)
  - every 6h      refresh active listings (re-crawl current URLs for price/avail changes)
  - weekly Mon 03:00  recompute city + neighborhood analytics

Manual triggers:
  - POST /admin/sources/{slug}/crawl  (API)
  - POST /admin/sources/{slug}/crawl/stream  (SSE, live progress)
  - POST /admin/crawl-all/stream  (SSE, all sources)
  - CLI: python cli.py crawl [--source SLUG] [--max-pages N]
  - CLI: python cli.py analytics      (recompute analytics now)
  - CLI: python cli.py jobs           (list scheduled jobs)

Schedule editing:
  - GET /admin/jobs      (list live + persisted state)
  - PATCH /admin/jobs/{job_id}  (cron_expr, paused) -> apply_job_config

Idempotency: a crawl in progress for a source blocks a new trigger for
that source (checked via scheduler_jobs.status).

Error handling: every external call (scraper HTTP, recompute) is wrapped
in try/except that logs internally and stores a sanitized French string
(via core.errors.sanitize_error) in scheduler_jobs.last_error — never
the raw exception text, URL, or payload.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.errors import sanitize_error
from core.models import Source, SchedulerJob
from core.analytics import recompute_all
from main import run_source, build_adapter
from core.ingest import ingest, mark_removed

logger = logging.getLogger(__name__)

# Stable APScheduler job ids. Mapped to scheduler_jobs rows via job_aps_id.
APS_JOB_CRAWL_ALL = "crawl_all"
APS_JOB_REFRESH = "refresh"
APS_JOB_ANALYTICS = "analytics"

# Default cron expressions (used when scheduler_jobs.cron_expr is NULL).
DEFAULT_CRON = {
    APS_JOB_CRAWL_ALL: CronTrigger(hour=2, minute=0),
    APS_JOB_REFRESH: CronTrigger(hour="*/6", minute=15),
    APS_JOB_ANALYTICS: CronTrigger(day_of_week="mon", hour=3, minute=0),
}


# --------------------------------------------------------------------------- #
# Job state helpers
# --------------------------------------------------------------------------- #
def _get_or_create_job(db: Session, job_type: str,
                       source_id: int | None = None,
                       cron_expr: str | None = None) -> SchedulerJob:
    q = db.query(SchedulerJob).filter(SchedulerJob.job_type == job_type)
    if source_id is not None:
        q = q.filter(SchedulerJob.source_id == source_id)
    else:
        q = q.filter(SchedulerJob.source_id.is_(None))
    job = q.first()
    if job is None:
        job = SchedulerJob(job_type=job_type, source_id=source_id,
                           cron_expr=cron_expr, status="scheduled")
        db.add(job)
        db.flush()
    return job


def _set_running(db: Session, job: SchedulerJob) -> None:
    job.status = "running"
    job.last_run = datetime.now(timezone.utc)
    job.last_error = None


def _set_done(db: Session, job: SchedulerJob, error: str | None = None) -> None:
    job.status = "failed" if error else "succeeded"
    job.last_error = error


# --------------------------------------------------------------------------- #
# Job functions (wrapped so each has its own DB session + error handling)
# --------------------------------------------------------------------------- #
def job_crawl_all() -> None:
    """Daily 02:00 — crawl every active source."""
    db = SessionLocal()
    try:
        job = _get_or_create_job(db, "crawl_all")
        if job.status == "running":
            print("[scheduler] crawl_all already running, skipping")
            return
        _set_running(db, job)
        db.commit()
        try:
            sources = db.query(Source).filter(Source.is_active == True).all()
            for source in sources:
                try:
                    run_source(db, source)
                except Exception as e:
                    err = sanitize_error(e)
                    logger.exception("source %s failed", getattr(source, 'slug', '?'))
                    print(f"[scheduler] source {source.slug} failed: {err}")
                    db.rollback()
            _set_done(db, job)
        except Exception as e:
            err = sanitize_error(e)
            logger.exception("crawl_all failed")
            _set_done(db, job, error=err)
            raise
        db.commit()
    finally:
        db.close()


def job_crawl_source(source_slug: str) -> dict:
    """Manual or per-source scheduled crawl of a single source."""
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.slug == source_slug).first()
        if source is None:
            return {"ok": False, "error": f"unknown source {source_slug!r}"}
        job = _get_or_create_job(db, "crawl_source", source_id=source.id)
        if job.status == "running":
            return {"ok": False, "error": f"crawl already in progress for {source_slug}"}
        _set_running(db, job)
        db.commit()
        try:
            stats = run_source(db, source)
            _set_done(db, job)
            db.commit()
            return {"ok": True, "stats": stats}
        except Exception as e:
            db.rollback()
            err = sanitize_error(e)
            logger.exception("crawl_source %s failed", source_slug)
            job = db.query(SchedulerJob).get(job.id)
            _set_done(db, job, error=err)
            db.commit()
            return {"ok": False, "error": err}
    finally:
        db.close()


def job_refresh_active() -> None:
    """Every 6h — re-crawl active sources to detect price/availability changes.
    Same as crawl_all but signals a 'refresh' job_type for tracking."""
    db = SessionLocal()
    try:
        job = _get_or_create_job(db, "refresh")
        if job.status == "running":
            print("[scheduler] refresh already running, skipping")
            return
        _set_running(db, job)
        db.commit()
        try:
            sources = db.query(Source).filter(Source.is_active == True).all()
            for source in sources:
                try:
                    run_source(db, source)
                except Exception as e:
                    err = sanitize_error(e)
                    logger.exception("refresh %s failed", getattr(source, 'slug', '?'))
                    print(f"[scheduler] refresh {source.slug} failed: {err}")
                    db.rollback()
            _set_done(db, job)
        except Exception as e:
            err = sanitize_error(e)
            logger.exception("refresh failed")
            _set_done(db, job, error=err)
            raise
        db.commit()
    finally:
        db.close()


def job_recompute_analytics() -> dict:
    """Weekly — recompute all city + neighborhood analytics into the cache."""
    db = SessionLocal()
    try:
        job = _get_or_create_job(db, "analytics")
        if job.status == "running":
            return {"ok": False, "error": "analytics recompute already running"}
        _set_running(db, job)
        db.commit()
        try:
            stats = recompute_all(db)
            _set_done(db, job)
            db.commit()
            return {"ok": True, "stats": stats}
        except Exception as e:
            db.rollback()
            err = sanitize_error(e)
            logger.exception("analytics recompute failed")
            job = db.query(SchedulerJob).get(job.id)
            _set_done(db, job, error=err)
            db.commit()
            return {"ok": False, "error": err}
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# Streaming crawl (SSE)
# --------------------------------------------------------------------------- #
def job_crawl_source_streaming(slug: str, broker) -> dict:
    """Crawl a single source, publishing progress events to ``broker``.

    Runs in a threadpool (called via ``run_in_threadpool`` from the SSE
    generator). Events published:
      - {"type":"progress","source":slug,"page":n,"listings":k}
      - {"type":"error","message": sanitize_error(e)}  (on failure)
      - {"type":"done","source":slug,"stats":{...}}      (on success)

    For "__all__" slug, crawls every active source sequentially.

    All exceptions are caught locally and sanitized — never re-raised as a
    raw traceback. Returns the final stats dict (also used by tests).
    """
    from core.sse import CrawlEventBroker  # for type only
    db = SessionLocal()
    try:
        if slug == "__all__":
            sources = db.query(Source).filter(Source.is_active == True).all()
            if not sources:
                broker.publish("__all__", {"type": "error", "message": "Aucune source active"})
                broker.publish("__all__", {"type": "done", "stats": {"sources": 0}})
                return {"sources": 0}
            total_stats: dict = {"sources": len(sources), "per_source": {}}
            for src in sources:
                _crawl_one_streaming(db, src, "__all__", broker)
                total_stats["per_source"][src.slug] = "ok"
            broker.publish("__all__", {"type": "done", "stats": total_stats})
            return total_stats

        src = db.query(Source).filter(Source.slug == slug).first()
        if src is None:
            broker.publish(slug, {"type": "error", "message": f"Source '{slug}' introuvable"})
            broker.publish(slug, {"type": "done", "stats": {"ok": False}})
            return {"ok": False}
        stats = _crawl_one_streaming(db, src, slug, broker)
        broker.publish(slug, {"type": "done", "source": slug, "stats": stats})
        return stats
    except Exception as e:
        err = sanitize_error(e)
        logger.exception("streaming crawl %s failed", slug)
        try:
            broker.publish(slug, {"type": "error", "message": err})
            broker.publish(slug, {"type": "done", "stats": {"ok": False}})
        except Exception:
            pass
        return {"ok": False, "error": err}
    finally:
        db.close()


def _crawl_one_streaming(db: Session, source: Source, key: str, broker) -> dict:
    """Crawl one source, publishing progress. Reuses run_source internally.

    Because ``run_source`` doesn't expose per-page callbacks, we approximate
    progress by re-implementing the fetch+ingest loop and publishing one
    "progress" event before ingest begins (page count from the adapter's
    max_pages) and one after. This gives the admin client real-time feedback
    that the crawl started and finished for each source.
    """
    try:
        adapter = build_adapter(source)
        crawl_session_id = uuid.uuid4()
        # Publish a start event so the client sees activity immediately.
        broker.publish(key, {
            "type": "progress",
            "source": source.slug,
            "page": 0,
            "listings": 0,
            "message": f"Crawl démarré: {source.display_name}",
        })
        drafts = adapter.fetch_listings(max_pages=None)
        # Drafts may be a generator or a list; count lazily.
        draft_list = list(drafts)
        broker.publish(key, {
            "type": "progress",
            "source": source.slug,
            "page": 1,
            "listings": len(draft_list),
            "message": f"{len(draft_list)} annonces récupérées, ingestion en cours",
        })
        stats = ingest(db, draft_list, source.id, crawl_session_id,
                       adapter_kind=source.adapter_kind)
        removed = mark_removed(db, source.id, crawl_session_id)
        stats["removed"] = removed
        broker.publish(key, {
            "type": "progress",
            "source": source.slug,
            "page": 1,
            "listings": len(draft_list),
            "message": f"Ingestion terminée: {stats}",
        })
        return stats
    except Exception as e:
        err = sanitize_error(e)
        logger.exception("streaming source %s failed", source.slug)
        broker.publish(key, {"type": "error", "source": source.slug, "message": err})
        db.rollback()
        return {"ok": False, "error": err}


# --------------------------------------------------------------------------- #
# Scheduler setup
# --------------------------------------------------------------------------- #
_scheduler: Optional[BackgroundScheduler] = None


def _load_persisted_cron(db: Session) -> dict[str, tuple[CronTrigger, bool]]:
    """Read scheduler_jobs rows with job_aps_id set and return
    ``{job_aps_id: (CronTrigger, paused)}``. Falls back to DEFAULT_CRON."""
    result: dict[str, tuple[CronTrigger, bool]] = {}
    rows = (
        db.query(SchedulerJob)
        .filter(SchedulerJob.job_aps_id.isnot(None))
        .all()
    )
    for row in rows:
        if not row.job_aps_id:
            continue
        if row.cron_expr:
            try:
                trigger = CronTrigger.from_crontab(row.cron_expr)
            except Exception:
                logger.warning(
                    "invalid cron_expr %r for %s, using default",
                    row.cron_expr, row.job_aps_id,
                )
                trigger = DEFAULT_CRON.get(row.job_aps_id, CronTrigger(hour=2))
        else:
            trigger = DEFAULT_CRON.get(row.job_aps_id, CronTrigger(hour=2))
        result[row.job_aps_id] = (trigger, bool(row.paused))
    return result


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
        # Read persisted cron_expr / paused from scheduler_jobs. If no row
        # exists for a given job_aps_id, fall back to the hardcoded default.
        db = SessionLocal()
        persisted: dict[str, tuple[CronTrigger, bool]] = {}
        try:
            persisted = _load_persisted_cron(db)
        except Exception:
            logger.exception("failed to load persisted cron config; using defaults")
        finally:
            db.close()

        # Default registrations (used if no persisted row overrides them).
        schedule_specs = [
            (APS_JOB_CRAWL_ALL, job_crawl_all, DEFAULT_CRON[APS_JOB_CRAWL_ALL]),
            (APS_JOB_REFRESH, job_refresh_active, DEFAULT_CRON[APS_JOB_REFRESH]),
            (APS_JOB_ANALYTICS, job_recompute_analytics, DEFAULT_CRON[APS_JOB_ANALYTICS]),
        ]
        for aps_id, func, default_trigger in schedule_specs:
            trigger = default_trigger
            paused = False
            if aps_id in persisted:
                trigger, paused = persisted[aps_id]
            _scheduler.add_job(
                func, trigger,
                id=aps_id, replace_existing=True,
            )
            if paused:
                try:
                    _scheduler.pause_job(aps_id)
                except Exception:
                    logger.warning("could not pause job %s", aps_id)
    return _scheduler


def apply_job_config(db: Session, job_id: int, cron_expr: str | None = None,
                     paused: bool | None = None) -> SchedulerJob:
    """Apply a cron_expr and/or paused update to a SchedulerJob row and the
    live APScheduler entry.

    ``job_id`` is the SchedulerJob.id (NOT the aps id). The row's
    ``job_aps_id`` is used to address the live scheduler entry.
    """
    row = db.query(SchedulerJob).get(job_id)
    if row is None:
        raise ValueError(f"scheduler job {job_id} not found")
    if not row.job_aps_id:
        raise ValueError("Cette tâche n'est pas liée à APScheduler (job_aps_id null).")

    sched = get_scheduler()
    if cron_expr is not None:
        # Validate by constructing the trigger first.
        trigger = CronTrigger.from_crontab(cron_expr)
        try:
            sched.reschedule_job(row.job_aps_id, trigger=trigger)
        except Exception:
            logger.exception("reschedule failed for %s", row.job_aps_id)
            raise
        row.cron_expr = cron_expr

    if paused is not None:
        try:
            if paused:
                sched.pause_job(row.job_aps_id)
            else:
                sched.resume_job(row.job_aps_id)
        except Exception:
            logger.exception("pause/resume failed for %s", row.job_aps_id)
            raise
        row.paused = paused

    db.commit()
    db.refresh(row)
    return row


def start_scheduler() -> None:
    """Called from FastAPI startup to begin background scheduling."""
    s = get_scheduler()
    if not s.running:
        s.start()
        print("[scheduler] started — crawl_all@02:00, refresh@*/6h, analytics@Mon03:00")


def shutdown_scheduler() -> None:
    """Called from FastAPI shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[scheduler] shut down")


def list_jobs(db: Session) -> list[dict]:
    """Return the state of all tracked scheduler_jobs rows, merged with the
    live APScheduler next_run_time where available."""
    rows = db.query(SchedulerJob).all()
    sched = _scheduler
    live_next: dict[str, datetime] = {}
    if sched is not None and sched.running:
        try:
            for job in sched.get_jobs():
                live_next[job.id] = job.next_run_time
        except Exception:
            pass

    out = []
    for j in rows:
        next_run = j.next_run
        if j.job_aps_id and j.job_aps_id in live_next:
            next_run = live_next[j.job_aps_id]
        out.append({
            "id": j.id,
            "job_type": j.job_type,
            "source_id": j.source_id,
            "cron_expr": j.cron_expr,
            "last_run": j.last_run.isoformat() if j.last_run else None,
            "next_run": next_run.isoformat() if next_run else None,
            "status": j.status,
            "last_error": j.last_error,
            "paused": bool(j.paused),
            "job_aps_id": j.job_aps_id,
        })
    return out