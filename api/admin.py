"""Admin endpoints — review pending listings, manage sources, view jobs.

All endpoints require an admin JWT (``Depends(require_admin)``). Login is
via ``POST /admin/login`` (api/admin_auth.py), which issues the JWT after
verifying the admin's email/username + password against the
``admin_users`` table.

Live crawler control is exposed via two SSE streaming endpoints that
publish per-source progress events from the scheduler.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.admin_auth import require_admin
from core.database import get_db, SessionLocal
from core.models import Source, RawListing, CanonicalProperty, Location, SchedulerJob, AdminUser
from core.ingest import promote_raw_listing, create_canonical, resolve_location, explanation_dict
from core.scheduler import (
    job_crawl_source, job_recompute_analytics, list_jobs,
    apply_job_config, job_crawl_source_streaming, get_scheduler,
)
from core.sse import broker, format_sse
from core.schemas import (
    SourceSchema, ReviewAction, SchedulerJobSchema, CrawlResult,
    JobUpdateSchema, JobSchemaOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# --------------------------------------------------------------------------- #
# Dashboard — system overview stats
# --------------------------------------------------------------------------- #
@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Return aggregate system stats for the admin dashboard."""
    from sqlalchemy import func

    total_raw = db.query(func.count(RawListing.id)).scalar() or 0
    total_canonicals = db.query(func.count(CanonicalProperty.id)).scalar() or 0
    active_canonicals = db.query(func.count(CanonicalProperty.id)).filter(
        CanonicalProperty.is_active == True
    ).scalar() or 0
    total_sources = db.query(func.count(Source.id)).scalar() or 0
    active_sources = db.query(func.count(Source.id)).filter(
        Source.is_active == True
    ).scalar() or 0
    pending_count = db.query(func.count(RawListing.id)).filter(
        RawListing.review_status == "pending"
    ).scalar() or 0
    unique_cities = db.query(func.count(func.distinct(Location.city))).scalar() or 0
    unique_neighborhoods = db.query(func.count(Location.id)).filter(
        Location.neighborhood.isnot(None)
    ).scalar() or 0
    location_count = db.query(func.count(Location.id)).scalar() or 0

    # Price stats
    price_stats = db.query(
        func.min(CanonicalProperty.current_best_price),
        func.avg(CanonicalProperty.current_best_price),
        func.max(CanonicalProperty.current_best_price),
    ).filter(
        CanonicalProperty.current_best_price.isnot(None),
        CanonicalProperty.current_best_price > 0,
        CanonicalProperty.is_active == True,
    ).first()

    # Property type distribution
    type_rows = db.query(
        CanonicalProperty.property_type,
        func.count(CanonicalProperty.id),
    ).filter(
        CanonicalProperty.is_active == True,
    ).group_by(CanonicalProperty.property_type).order_by(
        func.count(CanonicalProperty.id).desc()
    ).all()

    # Listing purpose split
    rent_count = db.query(func.count(CanonicalProperty.id)).filter(
        CanonicalProperty.is_active == True,
        CanonicalProperty.listing_purpose == "rent",
    ).scalar() or 0
    sale_count = db.query(func.count(CanonicalProperty.id)).filter(
        CanonicalProperty.is_active == True,
        CanonicalProperty.listing_purpose != "rent",
    ).scalar() or 0

    # Top cities by listing count
    city_rows = db.query(
        Location.city,
        func.count(CanonicalProperty.id).label("cnt"),
    ).join(
        CanonicalProperty, CanonicalProperty.location_id == Location.id
    ).filter(
        CanonicalProperty.is_active == True,
    ).group_by(Location.city).order_by(
        func.count(CanonicalProperty.id).desc()
    ).limit(8).all()

    # Jobs summary
    running_jobs = db.query(func.count(SchedulerJob.id)).filter(
        SchedulerJob.status == "running"
    ).scalar() or 0
    failed_jobs = db.query(func.count(SchedulerJob.id)).filter(
        SchedulerJob.status == "failed"
    ).scalar() or 0

    # Recent activity: listings added in last 24h and 7d
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    new_24h = db.query(func.count(RawListing.id)).filter(
        RawListing.crawled_at >= last_24h
    ).scalar() or 0
    new_7d = db.query(func.count(RawListing.id)).filter(
        RawListing.crawled_at >= last_7d
    ).scalar() or 0

    return {
        "counts": {
            "total_raw_listings": total_raw,
            "total_canonicals": total_canonicals,
            "active_canonicals": active_canonicals,
            "total_sources": total_sources,
            "active_sources": active_sources,
            "pending_review": pending_count,
            "unique_cities": unique_cities,
            "unique_neighborhoods": unique_neighborhoods,
            "total_locations": location_count,
        },
        "price_stats": {
            "min": price_stats[0] if price_stats else None,
            "avg": int(price_stats[1]) if price_stats and price_stats[1] else None,
            "max": price_stats[2] if price_stats else None,
        },
        "property_types": [
            {"type": t or "Autre", "count": c}
            for t, c in type_rows
        ],
        "purpose_split": {
            "rent": rent_count,
            "sale": sale_count,
        },
        "top_cities": [
            {"city": c, "count": cnt}
            for c, cnt in city_rows
        ],
        "jobs_summary": {
            "running": running_jobs,
            "failed": failed_jobs,
        },
        "recent_activity": {
            "last_24h": new_24h,
            "last_7d": new_7d,
        },
    }


# --------------------------------------------------------------------------- #
# Review (universal-scraper pending listings)
# --------------------------------------------------------------------------- #
@router.get("/review/pending")
def list_pending(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """List universal-scraper listings awaiting human review, with duplicate info."""
    rows = db.query(RawListing).filter(
        RawListing.review_status == "pending"
    ).order_by(RawListing.crawled_at.desc()).offset(skip).limit(limit).all()
    result = []
    for r in rows:
        match_explanation = r.match_explanation or {}
        classification = match_explanation.get("classification", "New Property") if isinstance(match_explanation, dict) else "New Property"
        is_duplicate = classification in ("Confirmed Match", "Probable Match")
        result.append({
            "id": r.id,
            "title_raw": r.title_raw,
            "price_parsed": r.price_parsed,
            "currency": r.currency,
            "location_raw": r.location_raw,
            "url_source": r.url_source,
            "match_confidence": r.match_confidence,
            "match_explanation": match_explanation,
            "is_duplicate": is_duplicate,
            "crawled_at": r.crawled_at.isoformat() if r.crawled_at else None,
        })
    return result


@router.post("/review/{raw_listing_id}", response_model=dict)
def review_listing(
    raw_listing_id: int,
    body: ReviewAction = Body(...),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Approve or reject a pending universal-scraper listing.

    approve: runs match resolution, creates/links canonical, backdates first_seen.
    reject: marks as rejected (raw_listing stays for audit).
    """
    result = promote_raw_listing(db, raw_listing_id, action=body.action)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "unknown error"))
    return result


@router.get("/review/duplicates")
def list_duplicates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """List auto-promoted listings flagged as duplicates, with matched
    canonical data for side-by-side human validation."""
    rows = (
        db.query(RawListing)
        .filter(
            RawListing.review_status == "auto_promoted",
            RawListing.match_explanation.isnot(None),
            RawListing.canonical_property_id.isnot(None),
            RawListing.match_explanation["classification"].astext.in_(
                ["Confirmed Match", "Probable Match"]
            ),
        )
        .order_by(RawListing.crawled_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    result = []
    for r in rows:
        me = r.match_explanation or {}

        canon = None
        if r.canonical_property_id:
            canon = (
                db.query(CanonicalProperty)
                .filter(CanonicalProperty.id == r.canonical_property_id)
                .first()
            )

        # Main image from this listing
        listing_image = None
        if r.images_raw and isinstance(r.images_raw, list) and len(r.images_raw) > 0:
            listing_image = r.images_raw[0]

        # Main image from another listing on the same canonical (for comparison)
        canon_image = None
        canon_bedrooms = None
        canon_bathrooms = None
        canon_area_sqm = None
        if canon:
            canon_bedrooms = canon.bedrooms
            canon_bathrooms = canon.bathrooms
            canon_area_sqm = canon.area_sqm
            other = (
                db.query(RawListing)
                .filter(
                    RawListing.canonical_property_id == canon.id,
                    RawListing.id != r.id,
                    RawListing.images_raw.isnot(None),
                )
                .first()
            )
            if other and other.images_raw and isinstance(other.images_raw, list) and len(other.images_raw) > 0:
                canon_image = other.images_raw[0]
            if not canon_image:
                # Fallback: any other listing on this canonical
                any_other = (
                    db.query(RawListing)
                    .filter(
                        RawListing.canonical_property_id == canon.id,
                        RawListing.id != r.id,
                    )
                    .first()
                )
                if any_other and any_other.images_raw and isinstance(any_other.images_raw, list) and len(any_other.images_raw) > 0:
                    canon_image = any_other.images_raw[0]

        result.append(
            {
                "id": r.id,
                "title_raw": r.title_raw,
                "price_parsed": r.price_parsed,
                "currency": r.currency,
                "location_raw": r.location_raw,
                "url_source": r.url_source,
                "match_confidence": r.match_confidence,
                "match_explanation": me,
                "image_main": listing_image,
                "crawled_at": r.crawled_at.isoformat() if r.crawled_at else None,
                "canonical": {
                    "id": canon.id,
                    "title": canon.title_canonical,
                    "price": canon.current_best_price,
                    "bedrooms": canon_bedrooms,
                    "bathrooms": canon_bathrooms,
                    "area_sqm": canon_area_sqm,
                    "image_main": canon_image,
                }
                if canon
                else None,
            }
        )
    return result


@router.post("/review/duplicates/{raw_listing_id}", response_model=dict)
def review_duplicate(
    raw_listing_id: int,
    body: ReviewAction = Body(...),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Validate a duplicate match.

    confirm_duplicate: keep the existing link, mark as human-validated.
    not_duplicate: unlink from the current canonical, create a brand-new
                   canonical property for this listing.
    """
    from scrapers.drafts import RawListingDraft

    raw = db.query(RawListing).filter(RawListing.id == raw_listing_id).first()
    if raw is None:
        raise HTTPException(404, "raw_listing not found")
    if raw.canonical_property_id is None:
        raise HTTPException(400, "listing is not linked to a canonical property")

    action = body.action

    if action == "confirm_duplicate":
        me = dict(raw.match_explanation or {})
        me["human_validated"] = True
        raw.match_explanation = me
        db.commit()
        return {"ok": True, "action": "confirm_duplicate",
                "canonical_property_id": raw.canonical_property_id}

    if action == "not_duplicate":
        # Rebuild draft and create a fresh canonical property
        payload = raw.payload or {}
        draft = RawListingDraft(
            url_source=raw.url_source,
            title_raw=raw.title_raw,
            price_raw=raw.price_raw,
            price_parsed=raw.price_parsed,
            currency=raw.currency or "XAF",
            location_raw=raw.location_raw,
            description_raw=raw.description_raw,
            property_type_raw=raw.property_type_raw,
            images_raw=raw.images_raw or [],
            bedrooms=payload.get("bedrooms"),
            bathrooms=payload.get("bathrooms"),
            area_sqm=payload.get("area_sqm"),
            confidence=raw.match_confidence or 0.0,
            payload=payload,
        )
        location_id = resolve_location(db, raw.location_raw)
        canon = create_canonical(db, draft, location_id)
        db.flush()

        old_canon_id = raw.canonical_property_id

        # Re-point the raw listing to the new canonical
        raw.canonical_property_id = canon.id
        raw.review_status = "human_approved"

        # Re-write match_explanation
        me = dict(raw.match_explanation or {})
        me["human_validated"] = True
        me["human_decision"] = "not_duplicate"
        me["old_canonical_id"] = old_canon_id
        raw.match_explanation = me

        # Move first_seen history to the new canonical
        from core.models import ListingHistory
        db.query(ListingHistory).filter(
            ListingHistory.raw_listing_id == raw.id,
            ListingHistory.canonical_property_id == old_canon_id,
        ).update({ListingHistory.canonical_property_id: canon.id})

        # Ensure there's a first_seen on the new canonical
        has_fs = (
            db.query(ListingHistory)
            .filter(
                ListingHistory.canonical_property_id == canon.id,
                ListingHistory.raw_listing_id == raw.id,
                ListingHistory.event_type == "first_seen",
            )
            .count()
        )
        if has_fs == 0:
            db.add(ListingHistory(
                raw_listing_id=raw.id,
                canonical_property_id=canon.id,
                event_type="first_seen",
                price_observed=raw.price_parsed,
                availability="available",
                observed_at=raw.crawled_at,
                crawl_session_id=raw.crawl_session_id,
            ))

        db.commit()
        return {"ok": True, "action": "not_duplicate",
                "canonical_property_id": canon.id,
                "old_canonical_property_id": old_canon_id}

    raise HTTPException(400, f"unknown action {action!r} — use confirm_duplicate or not_duplicate")


# --------------------------------------------------------------------------- #
# Sources management
# --------------------------------------------------------------------------- #
@router.get("/sources", response_model=List[SourceSchema])
def list_sources(db: Session = Depends(get_db),
                 _admin: AdminUser = Depends(require_admin)):
    return db.query(Source).order_by(Source.id).all()


@router.post("/sources", response_model=SourceSchema)
def create_source(src: SourceSchema, db: Session = Depends(get_db),
                   _admin: AdminUser = Depends(require_admin)):
    existing = db.query(Source).filter(Source.slug == src.slug).first()
    if existing:
        raise HTTPException(409, f"Source slug '{src.slug}' already exists")
    new = Source(
        slug=src.slug,
        display_name=src.display_name,
        site_url=src.site_url,
        adapter_kind=src.adapter_kind,
        is_active=src.is_active,
        crawl_config=src.crawl_config or {},
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.post("/sources/{slug}/crawl", response_model=CrawlResult)
def trigger_crawl(slug: str, _admin: AdminUser = Depends(require_admin)):
    """Manually trigger a crawl for one source."""
    result = job_crawl_source(slug)
    return CrawlResult(**result)


@router.post("/sources/{slug}/crawl/stream")
async def crawl_source_stream(slug: str,
                               _admin: AdminUser = Depends(require_admin)):
    """SSE stream of per-source crawl progress.

    The crawl runs in a threadpool; events flow through the
    ``CrawlEventBroker`` to the generator's asyncio.Queue.
    """
    queue = broker.subscribe(slug)

    async def event_generator():
        # Kick off the crawl in a worker thread. We don't await it here —
        # the generator drains the queue until a "done" event arrives.
        asyncio.ensure_future(
            run_in_threadpool(job_crawl_source_streaming, slug, broker)
        )
        try:
            while True:
                event = await queue.get()
                yield format_sse(event.get("type", "message"), event)
                if event.get("type") == "done":
                    break
        finally:
            broker.unsubscribe(slug, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/sources/{slug}/crawl/test/stream")
async def crawl_test_stream(
    slug: str,
    max_pages: int = Query(1, ge=1, le=50, description="Max pages to crawl (default: 1)"),
    _admin: AdminUser = Depends(require_admin),
):
    """SSE stream of a TEST crawl — fetches listings WITHOUT persisting to DB.

    Each listing is streamed as a ``listing`` SSE event with full data
    (title, price, location, images, raw payload/HTML). A final ``done``
    event carries summary stats.

    Set ``max_pages`` to control how many pages the adapter fetches.
    """
    from main import build_adapter
    from scrapers.drafts import RawListingDraft

    db = SessionLocal()
    try:
        src = db.query(Source).filter(Source.slug == slug).first()
    finally:
        db.close()

    if not src:
        async def err_gen():
            yield format_sse("error", {"type": "error", "message": f"Source '{slug}' introuvable"})
            yield format_sse("done", {"type": "done", "stats": {"ok": False}})
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    queue = broker.subscribe(slug)

    def _run_test_crawl():
        try:
            broker.publish(slug, {
                "type": "progress",
                "source": slug,
                "page": 0,
                "listings": 0,
                "message": f"Crawl TEST démarré: {src.display_name} (max_pages={max_pages}, sans persistence DB)",
            })
            adapter = build_adapter(src)
            drafts = list(adapter.fetch_listings(max_pages=max_pages))
            total = len(drafts)

            broker.publish(slug, {
                "type": "progress",
                "source": slug,
                "page": 1,
                "listings": total,
                "message": f"{total} annonces récupérées, envoi des données...",
            })

            # Stream each listing as a dedicated SSE event
            for i, draft in enumerate(drafts):
                listing_data = {
                    "index": i + 1,
                    "url_source": getattr(draft, "url_source", None),
                    "title_raw": getattr(draft, "title_raw", None),
                    "price_raw": str(getattr(draft, "price_raw", "")) if getattr(draft, "price_raw", None) else None,
                    "price_parsed": getattr(draft, "price_parsed", None),
                    "currency": getattr(draft, "currency", None),
                    "location_raw": getattr(draft, "location_raw", None),
                    "description_raw": getattr(draft, "description_raw", None),
                    "property_type_raw": getattr(draft, "property_type_raw", None),
                    "images_raw": getattr(draft, "images_raw", None) if hasattr(draft, "images_raw") else [],
                    "match_confidence": getattr(draft, "match_confidence", None),
                    "payload": getattr(draft, "payload", None) if hasattr(draft, "payload") else {},
                }
                broker.publish(slug, {
                    "type": "listing",
                    "source": slug,
                    **listing_data,
                })

            broker.publish(slug, {
                "type": "done",
                "source": slug,
                "stats": {
                    "ok": True,
                    "total": total,
                    "new": total,
                    "test": True,
                },
            })
        except Exception as e:
            from core.errors import sanitize_error
            err = sanitize_error(e)
            logger.exception("test crawl %s failed", slug)
            try:
                broker.publish(slug, {"type": "error", "source": slug, "message": err})
                broker.publish(slug, {"type": "done", "stats": {"ok": False}})
            except Exception:
                pass

    async def event_generator():
        asyncio.ensure_future(run_in_threadpool(_run_test_crawl))
        try:
            while True:
                event = await queue.get()
                yield format_sse(event.get("type", "message"), event)
                if event.get("type") == "done":
                    break
        finally:
            broker.unsubscribe(slug, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/crawl-all/stream")
async def crawl_all_stream(_admin: AdminUser = Depends(require_admin)):
    """SSE stream of crawl-all progress (every active source)."""
    key = "__all__"
    queue = broker.subscribe(key)

    async def event_generator():
        asyncio.ensure_future(
            run_in_threadpool(job_crawl_source_streaming, key, broker)
        )
        try:
            while True:
                event = await queue.get()
                yield format_sse(event.get("type", "message"), event)
                if event.get("type") == "done":
                    break
        finally:
            broker.unsubscribe(key, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/sources/{slug}/toggle", response_model=SourceSchema)
def toggle_source(slug: str, db: Session = Depends(get_db),
                   _admin: AdminUser = Depends(require_admin)):
    src = db.query(Source).filter(Source.slug == slug).first()
    if not src:
        raise HTTPException(404, f"Source '{slug}' not found")
    src.is_active = not src.is_active
    db.commit()
    db.refresh(src)
    return src


# --------------------------------------------------------------------------- #
# Crawl sessions & payload inspection
# --------------------------------------------------------------------------- #
@router.get("/sources/{slug}/crawl/sessions")
def list_crawl_sessions(
    slug: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """List recent crawl sessions for a source with aggregated stats."""
    from sqlalchemy import func

    src = db.query(Source).filter(Source.slug == slug).first()
    if not src:
        raise HTTPException(404, f"Source '{slug}' not found")

    subq = (
        db.query(
            RawListing.crawl_session_id,
            func.count(RawListing.id).label("total_listings"),
            func.sum(
                func.cast((RawListing.review_status == "pending"), type_=func.Integer)
            ).label("pending_count"),
            func.sum(
                func.cast((RawListing.review_status == "auto_promoted"), type_=func.Integer)
            ).label("auto_promoted"),
            func.sum(
                func.cast((RawListing.review_status == "rejected"), type_=func.Integer)
            ).label("rejected"),
            func.min(RawListing.crawled_at).label("started_at"),
        )
        .filter(RawListing.source_id == src.id)
        .group_by(RawListing.crawl_session_id)
        .order_by(func.min(RawListing.crawled_at).desc())
        .limit(limit)
        .all()
    )

    results = []
    for row in subq:
        session_id = str(row.crawl_session_id) if row.crawl_session_id else "unknown"
        dup_count = (
            db.query(func.count(RawListing.id))
            .filter(
                RawListing.source_id == src.id,
                RawListing.crawl_session_id == row.crawl_session_id,
                RawListing.match_explanation.isnot(None),
            )
            .scalar() or 0
        )
        # Deduplicate by checking match_explanation classification
        confirmed_dupes = 0
        if dup_count > 0:
            listings = (
                db.query(RawListing.match_explanation)
                .filter(
                    RawListing.source_id == src.id,
                    RawListing.crawl_session_id == row.crawl_session_id,
                    RawListing.match_explanation.isnot(None),
                )
                .all()
            )
            for (me,) in listings:
                if isinstance(me, dict) and me.get("classification") in ("Confirmed Match", "Probable Match"):
                    confirmed_dupes += 1

        new_count = row.total_listings - confirmed_dupes - (row.rejected or 0)
        results.append({
            "crawl_session_id": session_id,
            "source_slug": slug,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "total_listings": row.total_listings,
            "new_listings": max(new_count, 0),
            "duplicates": confirmed_dupes,
            "pending_count": row.pending_count or 0,
            "auto_promoted": row.auto_promoted or 0,
            "rejected": row.rejected or 0,
            "status": "completed",
        })
    return results


@router.get("/raw-listings/{raw_id}/payload")
def get_raw_listing_payload(
    raw_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Return the full extraction payload (including raw HTML) for a raw listing."""
    raw = db.query(RawListing).filter(RawListing.id == raw_id).first()
    if not raw:
        raise HTTPException(404, "Raw listing not found")
    return {
        "id": raw.id,
        "url_source": raw.url_source,
        "title_raw": raw.title_raw,
        "payload": raw.payload or {},
    }


# --------------------------------------------------------------------------- #
# Analytics
# --------------------------------------------------------------------------- #
@router.post("/analytics/recompute", response_model=CrawlResult)
def trigger_analytics(_admin: AdminUser = Depends(require_admin)):
    """Manually recompute all neighborhood analytics."""
    result = job_recompute_analytics()
    return CrawlResult(**result)


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
@router.get("/jobs")
def get_jobs(db: Session = Depends(get_db),
             _admin: AdminUser = Depends(require_admin)):
    """List tracked scheduler jobs merged with live APScheduler state."""
    return list_jobs(db)


@router.patch("/jobs/{job_id}", response_model=JobSchemaOut)
def patch_job(job_id: int, body: JobUpdateSchema = Body(...),
              db: Session = Depends(get_db),
              _admin: AdminUser = Depends(require_admin)):
    """Update a job's cron_expr and/or paused flag."""
    try:
        row = apply_job_config(db, job_id,
                               cron_expr=body.cron_expr,
                               paused=body.paused)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("apply_job_config failed")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
    # Compute next_run from the live scheduler.
    sched = get_scheduler()
    next_run = None
    if row.job_aps_id:
        try:
            live = sched.get_job(row.job_aps_id)
            if live is not None:
                next_run = live.next_run_time
        except Exception:
            pass
    return JobSchemaOut(
        id=row.id,
        job_type=row.job_type,
        source_id=row.source_id,
        cron_expr=row.cron_expr,
        last_run=row.last_run,
        next_run=next_run,
        status=row.status,
        last_error=row.last_error,
        paused=bool(row.paused),
        job_aps_id=row.job_aps_id,
    )