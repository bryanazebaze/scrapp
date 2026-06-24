"""Market-intelligence computation.

Aggregates canonical_properties + listing_history into per-city and
per-neighborhood stats and writes them to the neighborhood_analytics cache
table. The scheduler recomputes this weekly; `GET /neighborhoods/{slug}`
reads from the cache plus a live delta (Phase 7).

All scores are computed via core.scoring from platform data only.
"""
from __future__ import annotations

import statistics
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.models import (
    CanonicalProperty, Location, ListingHistory, NeighborhoodAnalytics,
)
from . import scoring


HIGH_END_AMENITY_TERMS = ("pool", "piscine", "garden", "jardin", "garage",
                           "terrace", "terrasse", "elevator", "ascenseur",
                           "view", "vue", "sea", "mer")


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _median(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return statistics.median(values)


def _percentile(sorted_vals: list[float], pct: float) -> Optional[float]:
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _days_between(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds()) / 86400.0


# --------------------------------------------------------------------------- #
# Stats collection
# --------------------------------------------------------------------------- #
def _location_canonicals(db: Session, location: Location,
                         property_type: str | None) -> list[CanonicalProperty]:
    """Fetch canonical properties for a location. City-level locations
    (neighborhood NULL) aggregate across all neighborhoods of that city."""
    q = db.query(CanonicalProperty).join(Location,
                                          CanonicalProperty.location_id == Location.id)
    if location.neighborhood is None:
        # city-level: all neighborhoods of this city
        q = q.filter(Location.city == location.city)
    else:
        q = q.filter(CanonicalProperty.location_id == location.id)
    q = q.filter(CanonicalProperty.current_best_price.isnot(None))
    if property_type:
        q = q.filter(CanonicalProperty.property_type == property_type)
    return q.all()


def _median_days_on_market(db: Session, canon_ids: list[int]) -> Optional[float]:
    """Median days between first_seen and removed for the given canonicals."""
    if not canon_ids:
        return None
    durations: list[float] = []
    for cid in canon_ids:
        first = db.query(ListingHistory).filter(
            ListingHistory.canonical_property_id == cid,
            ListingHistory.event_type == "first_seen",
        ).order_by(ListingHistory.observed_at.asc()).first()
        removed = db.query(ListingHistory).filter(
            ListingHistory.canonical_property_id == cid,
            ListingHistory.event_type == "removed",
        ).order_by(ListingHistory.observed_at.desc()).first()
        if first and removed and removed.observed_at > first.observed_at:
            durations.append(_days_between(removed.observed_at, first.observed_at))
    return _median(durations) if durations else None


def _trend_pct(db: Session, canon_ids: list[int], days: int = 90) -> Optional[float]:
    """Percent change in mean first_seen price between the last `days` window
    and the preceding one. Positive = prices rising."""
    if not canon_ids:
        return None
    now = datetime.now(timezone.utc)
    mid = now - timedelta(days=days)
    start = now - timedelta(days=2 * days)
    recent = []
    prior = []
    for cid in canon_ids:
        ev = db.query(ListingHistory).filter(
            ListingHistory.canonical_property_id == cid,
            ListingHistory.event_type == "first_seen",
        ).first()
        if not ev or ev.price_observed is None:
            continue
        if mid <= ev.observed_at <= now:
            recent.append(ev.price_observed)
        elif start <= ev.observed_at < mid:
            prior.append(ev.price_observed)
    if not recent or not prior:
        return None
    r, p = statistics.mean(recent), statistics.mean(prior)
    if p == 0:
        return None
    return ((r - p) / p) * 100.0


def _listings_per_week(db: Session, location: Location,
                       property_type: str | None, days: int = 90) -> Optional[float]:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    q = db.query(func.count(ListingHistory.id)).join(
        CanonicalProperty, ListingHistory.canonical_property_id == CanonicalProperty.id
    ).join(Location, CanonicalProperty.location_id == Location.id).filter(
        ListingHistory.event_type == "first_seen",
        ListingHistory.observed_at >= since,
    )
    if location.neighborhood is None:
        q = q.filter(Location.city == location.city)
    else:
        q = q.filter(CanonicalProperty.location_id == location.id)
    if property_type:
        q = q.filter(CanonicalProperty.property_type == property_type)
    count = q.scalar() or 0
    return count / (days / 7.0) if days > 0 else None


def _amenity_share(drafts_payloads: list[dict]) -> Optional[float]:
    """Fraction of listings whose description/amenities mention a high-end
    amenity term."""
    if not drafts_payloads:
        return None
    hit = 0
    for p in drafts_payloads:
        text = " ".join(str(v) for v in (p or {}).values()).lower()
        if any(t in text for t in HIGH_END_AMENITY_TERMS):
            hit += 1
    return hit / len(drafts_payloads)


# --------------------------------------------------------------------------- #
# Per-location analytics row
# --------------------------------------------------------------------------- #
def compute_for_location(db: Session, location: Location,
                         city_median_price: float | None,
                         property_type: str | None = None) -> dict | None:
    """Compute the analytics dict for one location (+ optional property type).
    `city_median_price` is the median price across the whole city, used for
    the premium score normalization."""
    canons = _location_canonicals(db, location, property_type)
    if not canons:
        return None
    prices = sorted([c.current_best_price for c in canons
                     if c.current_best_price and c.current_best_price > 0])
    if not prices:
        return None
    canon_ids = [c.id for c in canons]

    avg = statistics.mean(prices)
    median = statistics.median(prices)
    pmin, pmax = prices[0], prices[-1]
    # price per sqm where area is known
    sqm_prices = [c.current_best_price / c.area_sqm for c in canons
                  if c.area_sqm and c.area_sqm > 0 and c.current_best_price]
    price_per_sqm = statistics.mean(sqm_prices) if sqm_prices else None

    dom = _median_days_on_market(db, canon_ids)
    trend = _trend_pct(db, canon_ids)
    per_week = _listings_per_week(db, location, property_type)

    # Top-decile share within the city.
    top_decile_share: Optional[float] = None
    if city_median_price is not None:
        top_count = sum(1 for p in prices if p >= city_median_price * 1.5)
        top_decile_share = top_count / len(prices)

    # Amenity share from raw listing payloads.
    from core.models import RawListing
    payloads = [r.payload for r in db.query(RawListing).filter(
        RawListing.canonical_property_id.in_(canon_ids)).all()]
    amen_share = _amenity_share(payloads)

    prem = scoring.premium_score(median, city_median_price)
    dem = scoring.demand_score(dom)
    gro = scoring.growth_score(trend)
    act = scoring.activity_score(per_week)
    lux = scoring.luxury_score(prem, top_decile_share, amen_share)

    return {
        "location_id": location.id,
        "property_type": property_type,
        "period": "current",
        "listing_count": len(prices),
        "average_price": int(avg),
        "median_price": int(median),
        "min_price": int(pmin),
        "max_price": int(pmax),
        "price_per_sqm": round(price_per_sqm, 2) if price_per_sqm else None,
        "premium_score": prem,
        "demand_score": dem,
        "growth_score": gro,
        "activity_score": act,
        "luxury_score": lux,
        "trend_direction": ("up" if (trend or 0) > 1 else "down" if (trend or 0) < -1 else "flat"),
        "trend_pct": round(trend, 2) if trend is not None else None,
    }


# --------------------------------------------------------------------------- #
# City median helper
# --------------------------------------------------------------------------- #
def _city_median_price(db: Session, city: str) -> Optional[float]:
    rows = db.query(CanonicalProperty.current_best_price).join(
        Location, CanonicalProperty.location_id == Location.id
    ).filter(
        Location.city == city,
        CanonicalProperty.current_best_price.isnot(None),
    ).all()
    prices = sorted([r[0] for r in rows if r[0] and r[0] > 0])
    return statistics.median(prices) if prices else None


# --------------------------------------------------------------------------- #
# Full recompute
# --------------------------------------------------------------------------- #
def recompute_all(db: Session) -> dict:
    """Recompute analytics for every location and write to the
    neighborhood_analytics cache. Returns a stats dict."""
    stats = {"locations": 0, "rows_written": 0, "skipped": 0}
    locations = db.query(Location).all()
    # Precompute city medians for premium-score normalization.
    city_medians: dict[str, Optional[float]] = {}
    for loc in locations:
        if loc.city not in city_medians:
            city_medians[loc.city] = _city_median_price(db, loc.city)

    for loc in locations:
        stats["locations"] += 1
        # All-types row (property_type NULL) + per-type rows.
        seen_types = {c.property_type for c in _location_canonicals(db, loc, None)}
        for ptype in [None, *sorted(t for t in seen_types if t)]:
            row = compute_for_location(db, loc, city_medians.get(loc.city), ptype)
            if row is None:
                stats["skipped"] += 1
                continue
            _upsert_analytics(db, row)
            stats["rows_written"] += 1
    db.commit()
    return stats


def _upsert_analytics(db: Session, row: dict) -> None:
    existing = db.query(NeighborhoodAnalytics).filter(
        NeighborhoodAnalytics.location_id == row["location_id"],
        NeighborhoodAnalytics.property_type == row["property_type"],
        NeighborhoodAnalytics.period == row["period"],
    ).first()
    if existing:
        for k, v in row.items():
            setattr(existing, k, v)
        existing.computed_at = datetime.now(timezone.utc)
    else:
        db.add(NeighborhoodAnalytics(**row))


# --------------------------------------------------------------------------- #
# Read helpers for the API
# --------------------------------------------------------------------------- #
def get_location_analytics(db: Session, location_id: int,
                           property_type: str | None = None) -> NeighborhoodAnalytics | None:
    return db.query(NeighborhoodAnalytics).filter(
        NeighborhoodAnalytics.location_id == location_id,
        NeighborhoodAnalytics.property_type == property_type,
        NeighborhoodAnalytics.period == "current",
    ).first()


def find_location_by_slug(db: Session, slug: str) -> Location | None:
    return db.query(Location).filter(Location.slug == slug).first()