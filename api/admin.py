"""Admin endpoints — review pending listings, manage sources, view jobs."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Source, RawListing, SchedulerJob
from core.ingest import promote_raw_listing
from core.scheduler import job_crawl_source, job_recompute_analytics, list_jobs
from core.schemas import (
    SourceSchema, ReviewAction, SchedulerJobSchema, CrawlResult,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# --------------------------------------------------------------------------- #
# Review (universal-scraper pending listings)
# --------------------------------------------------------------------------- #
@router.get("/review/pending")
def list_pending(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List universal-scraper listings awaiting human review."""
    rows = db.query(RawListing).filter(
        RawListing.review_status == "pending"
    ).order_by(RawListing.crawled_at.desc()).offset(skip).limit(limit).all()
    return [{
        "id": r.id,
        "title_raw": r.title_raw,
        "price_parsed": r.price_parsed,
        "currency": r.currency,
        "location_raw": r.location_raw,
        "url_source": r.url_source,
        "match_confidence": r.match_confidence,
        "crawled_at": r.crawled_at.isoformat() if r.crawled_at else None,
    } for r in rows]


@router.post("/review/{raw_listing_id}", response_model=dict)
def review_listing(
    raw_listing_id: int,
    body: ReviewAction = Body(...),
    db: Session = Depends(get_db),
):
    """Approve or reject a pending universal-scraper listing.

    approve: runs match resolution, creates/links canonical, backdates first_seen.
    reject: marks as rejected (raw_listing stays for audit).
    """
    result = promote_raw_listing(db, raw_listing_id, action=body.action)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "unknown error"))
    return result


# --------------------------------------------------------------------------- #
# Sources management
# --------------------------------------------------------------------------- #
@router.get("/sources", response_model=List[SourceSchema])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).order_by(Source.id).all()


@router.post("/sources", response_model=SourceSchema)
def create_source(src: SourceSchema, db: Session = Depends(get_db)):
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
def trigger_crawl(slug: str):
    """Manually trigger a crawl for one source."""
    result = job_crawl_source(slug)
    return CrawlResult(**result)


@router.post("/sources/{slug}/toggle", response_model=SourceSchema)
def toggle_source(slug: str, db: Session = Depends(get_db)):
    src = db.query(Source).filter(Source.slug == slug).first()
    if not src:
        raise HTTPException(404, f"Source '{slug}' not found")
    src.is_active = not src.is_active
    db.commit()
    db.refresh(src)
    return src


# --------------------------------------------------------------------------- #
# Analytics
# --------------------------------------------------------------------------- #
@router.post("/analytics/recompute", response_model=CrawlResult)
def trigger_analytics():
    """Manually recompute all neighborhood analytics."""
    result = job_recompute_analytics()
    return CrawlResult(**result)


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
@router.get("/jobs", response_model=List[SchedulerJobSchema])
def get_jobs(db: Session = Depends(get_db)):
    return list_jobs(db)