"""APScheduler-based job scheduler, running in-process with FastAPI.

Jobs:
  - daily 02:00   crawl all active sources (dedicated + universal)
  - every 6h      refresh active listings (re-crawl current URLs for price/avail changes)
  - weekly Mon 03:00  recompute city + neighborhood analytics

Manual triggers:
  - POST /admin/sources/{slug}/crawl  (API)
  - CLI: python cli.py crawl [--source SLUG] [--max-pages N]
  - CLI: python cli.py analytics      (recompute analytics now)
  - CLI: python cli.py jobs           (list scheduled jobs)

Idempotency: a crawl in progress for a source blocks a new trigger for
that source (checked via scheduler_jobs.status).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.models import Source, SchedulerJob
from core.analytics import recompute_all
from main import run_source


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
                    print(f"[scheduler] source {source.slug} failed: {e}")
                    db.rollback()
            _set_done(db, job)
        except Exception as e:
            _set_done(db, job, error=str(e))
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
            # re-fetch job after rollback
            job = db.query(SchedulerJob).get(job.id)
            _set_done(db, job, error=str(e))
            db.commit()
            return {"ok": False, "error": str(e)}
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
                    print(f"[scheduler] refresh {source.slug} failed: {e}")
                    db.rollback()
            _set_done(db, job)
        except Exception as e:
            _set_done(db, job, error=str(e))
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
            job = db.query(SchedulerJob).get(job.id)
            _set_done(db, job, error=str(e))
            db.commit()
            return {"ok": False, "error": str(e)}
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# Scheduler setup
# --------------------------------------------------------------------------- #
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
        # Daily 02:00 UTC — full crawl of all active sources.
        _scheduler.add_job(
            job_crawl_all, CronTrigger(hour=2, minute=0),
            id="crawl_all", replace_existing=True,
        )
        # Every 6h — refresh active listings.
        _scheduler.add_job(
            job_refresh_active, CronTrigger(hour="*/6", minute=15),
            id="refresh", replace_existing=True,
        )
        # Weekly Monday 03:00 UTC — recompute analytics.
        _scheduler.add_job(
            job_recompute_analytics, CronTrigger(day_of_week="mon", hour=3, minute=0),
            id="analytics", replace_existing=True,
        )
    return _scheduler


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
    """Return the state of all tracked scheduler_jobs rows."""
    rows = db.query(SchedulerJob).all()
    return [{
        "id": j.id,
        "job_type": j.job_type,
        "source_id": j.source_id,
        "cron_expr": j.cron_expr,
        "last_run": j.last_run.isoformat() if j.last_run else None,
        "next_run": j.next_run.isoformat() if j.next_run else None,
        "status": j.status,
        "last_error": j.last_error,
    } for j in rows]