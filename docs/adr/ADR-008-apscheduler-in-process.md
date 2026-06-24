# ADR-008: APScheduler in-process over Celery

**Status**: Accepted
**Date**: 2026-06-20

## Context

The system needs scheduled automation: daily crawls, 6h refreshes, weekly analytics recompute. Two options:
1. **Celery + Redis**: a separate worker process + message broker. Production-grade, horizontally scalable.
2. **APScheduler in-process**: runs inside the FastAPI process via `BackgroundScheduler`. No external dependencies.

## Decision

Use **APScheduler in-process** (`apscheduler.schedulers.background.BackgroundScheduler`). The scheduler starts on FastAPI startup (`lifespan` context) and shuts down on app exit.

Jobs:
- **Daily 02:00 UTC**: `job_crawl_all` — crawl all active sources.
- **Every 6h**: `job_refresh_active` — re-crawl to detect price/availability changes.
- **Weekly Monday 03:00 UTC**: `job_recompute_analytics` — recompute all neighborhood scores.

Manual triggers: `POST /admin/sources/{slug}/crawl`, `POST /admin/analytics/recompute`, and `python cli.py crawl|analytics|jobs`.

## Rationale

- **Single-instance deployment**: CentralImmo runs on one server. No horizontal scaling needed yet. A separate Celery worker + Redis broker is operational overhead for no benefit.
- **No external dependency**: APScheduler is a Python library; no Redis/RabbitMQ to install, configure, and monitor.
- **Simple**: job functions are plain Python functions with their own DB session. The `scheduler_jobs` table tracks last run, status, and errors — visible at `GET /admin/jobs`.
- **Idempotency**: a crawl in progress for a source blocks a new trigger for that source (checked via `scheduler_jobs.status == 'running'`).

## Consequences

- If the FastAPI process crashes, scheduled jobs stop. Mitigation: the scheduler resumes on restart, and missed jobs can be triggered manually via CLI.
- When horizontal scaling is needed (multiple API instances), migrate to Celery. The job functions (`job_crawl_all`, etc.) are already isolated and can move to Celery tasks with minimal refactoring.
- The `scheduler_jobs` table provides visibility into job state — useful for debugging and for the admin UI.