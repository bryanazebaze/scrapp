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
    """
    loc = find_location_by_slug(db, slug)
    if not loc:
        raise HTTPException(404, f"Location '{slug}' not found")

    analytics = get_location_analytics(db, loc.id, property_type=property_type)
    if not analytics:
        raise HTTPException(404, "No analytics computed for this location yet. "
                            "Run `python cli.py analytics` or wait for the weekly recompute.")

    return NeighborhoodAnalyticsSchema(
        location_id=loc.id,
        city=loc.city,
        neighborhood=loc.neighborhood,
        slug=loc.slug,
        property_type=analytics.property_type,
        listing_count=analytics.listing_count,
        average_price=analytics.average_price,
        median_price=analytics.median_price,
        min_price=analytics.min_price,
        max_price=analytics.max_price,
        price_per_sqm=analytics.price_per_sqm,
        premium_score=analytics.premium_score,
        demand_score=analytics.demand_score,
        growth_score=analytics.growth_score,
        activity_score=analytics.activity_score,
        luxury_score=analytics.luxury_score,
        trend_direction=analytics.trend_direction,
        trend_pct=analytics.trend_pct,
    )


@router.get("/city/{city}", response_model=List[NeighborhoodAnalyticsSchema])
def get_city_neighborhoods(
    city: str,
    db: Session = Depends(get_db),
):
    """Analytics for all neighborhoods in a city (all-types rows)."""
    locs = db.query(Location).filter(Location.city == city).all()
    if not locs:
        raise HTTPException(404, f"No locations found for city '{city}'")
    results = []
    for loc in locs:
        a = get_location_analytics(db, loc.id)
        if a:
            results.append(NeighborhoodAnalyticsSchema(
                location_id=loc.id,
                city=loc.city,
                neighborhood=loc.neighborhood,
                slug=loc.slug,
                property_type=a.property_type,
                listing_count=a.listing_count,
                average_price=a.average_price,
                median_price=a.median_price,
                min_price=a.min_price,
                max_price=a.max_price,
                price_per_sqm=a.price_per_sqm,
                premium_score=a.premium_score,
                demand_score=a.demand_score,
                growth_score=a.growth_score,
                activity_score=a.activity_score,
                luxury_score=a.luxury_score,
                trend_direction=a.trend_direction,
                trend_pct=a.trend_pct,
            ))
    return results


@router.get("/trending/list", response_model=List[dict])
def trending_neighborhoods(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Neighborhoods ranked by growth_score (trending up)."""
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