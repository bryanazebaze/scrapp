"""Neighborhood market-intelligence endpoints."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Location, NeighborhoodAnalytics, CanonicalProperty
from core.analytics import find_location_by_slug, get_location_analytics
from core.schemas import NeighborhoodAnalyticsSchema, LocationSchema

router = APIRouter(prefix="/neighborhoods", tags=["neighborhoods"])


def _analytics_to_schema(loc: Location, a: NeighborhoodAnalytics) -> NeighborhoodAnalyticsSchema:
    """Build a NeighborhoodAnalyticsSchema from an ORM row (or transient row
    produced by _city_level_analytics) plus its Location."""
    fallback = getattr(a, "fallback_level", None)
    return NeighborhoodAnalyticsSchema(
        location_id=loc.id if loc is not None else a.location_id,
        city=loc.city if loc is not None else None,
        neighborhood=loc.neighborhood if loc is not None else None,
        slug=loc.slug if loc is not None else None,
        property_type=a.property_type,
        category=a.category,
        listing_count=a.listing_count or 0,
        average_price=a.average_price,
        median_price=a.median_price,
        min_price=a.min_price,
        max_price=a.max_price,
        price_per_sqm=a.price_per_sqm,
        min_price_per_sqm=a.min_price_per_sqm,
        max_price_per_sqm=a.max_price_per_sqm,
        avg_price_per_sqm=a.avg_price_per_sqm,
        fallback_level=fallback,
        premium_score=a.premium_score,
        demand_score=a.demand_score,
        growth_score=a.growth_score,
        activity_score=a.activity_score,
        luxury_score=a.luxury_score,
        trend_direction=a.trend_direction,
        trend_pct=a.trend_pct,
    )


@router.get("", response_model=List[LocationSchema])
def list_neighborhoods(
    city: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all known locations (cities + neighborhoods)."""
    q = db.query(Location)
    if city:
        q = q.filter(Location.city == city)
    return q.order_by(Location.city, Location.neighborhood).all()


@router.get("/{slug}", response_model=NeighborhoodAnalyticsSchema)
def get_neighborhood(
    slug: str,
    property_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Market intelligence for one neighborhood (or city-level if slug is a city).

    Returns cached analytics from neighborhood_analytics, recomputed weekly.
    When `property_type` is given, returns the per-type row with a geographic
    fallback to the city-level aggregate if the neighborhood has < 3 listings
    of that type (`fallback_level` reflects the source).
    """
    loc = find_location_by_slug(db, slug)
    if not loc:
        raise HTTPException(404, f"Location '{slug}' not found")

    analytics = get_location_analytics(db, loc.id, property_type=property_type)
    if not analytics:
        raise HTTPException(404, "No analytics computed for this location yet. "
                            "Run `python cli.py analytics` or wait for the weekly recompute.")

    return _analytics_to_schema(loc, analytics)


@router.get("/city/{city}", response_model=List[NeighborhoodAnalyticsSchema])
def get_city_neighborhoods(
    city: str,
    property_type: Optional[str] = Query(None,
        description="Filter to one property type; omit for per-type rows for each neighborhood"),
    db: Session = Depends(get_db),
):
    """Analytics for all neighborhoods in a city.

    When `property_type` is given, returns one row per neighborhood for that
    type (with city-level fallback when the neighborhood has < 3 listings of
    that type).

    When `property_type` is omitted, returns one row per
    (neighborhood, property_type) that has data — skipping the all-types pooled
    row, which is only used for trending. This gives callers a per-type market
    view for each neighborhood.
    """
    locs = db.query(Location).filter(Location.city == city).all()
    if not locs:
        raise HTTPException(404, f"No locations found for city '{city}'")

    results: list[NeighborhoodAnalyticsSchema] = []
    if property_type:
        for loc in locs:
            a = get_location_analytics(db, loc.id, property_type=property_type)
            if a:
                results.append(_analytics_to_schema(loc, a))
        return results

    # No property_type filter: emit per-type rows for each neighborhood.
    for loc in locs:
        rows = (
            db.query(NeighborhoodAnalytics)
            .filter(
                NeighborhoodAnalytics.location_id == loc.id,
                NeighborhoodAnalytics.property_type.isnot(None),
                NeighborhoodAnalytics.period == "current",
            )
            .all()
        )
        for a in rows:
            results.append(_analytics_to_schema(loc, a))
    return results


@router.get("/trending/list", response_model=List[dict])
def trending_neighborhoods(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Neighborhoods ranked by growth_score (trending up).

    Uses the all-types pooled row (property_type NULL) since trending is a
    cross-type signal by design.
    """
    rows = db.query(NeighborhoodAnalytics).filter(
        NeighborhoodAnalytics.property_type.is_(None),
        NeighborhoodAnalytics.growth_score.isnot(None),
    ).order_by(NeighborhoodAnalytics.growth_score.desc()).limit(limit).all()
    results = []
    for a in rows:
        loc = db.query(Location).filter(Location.id == a.location_id).first()
        if loc:
            results.append({
                "slug": loc.slug,
                "city": loc.city,
                "neighborhood": loc.neighborhood,
                "growth_score": a.growth_score,
                "trend_pct": a.trend_pct,
                "median_price": a.median_price,
            })
    return results