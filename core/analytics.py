"""Market-intelligence computation.

Aggregates canonical_properties + listing_history into per-city and
per-neighborhood stats and writes them to the neighborhood_analytics cache
table. The scheduler recomputes this weekly; `GET /neighborhoods/{slug}`
reads from the cache plus a live delta (Phase 7).

All scores are computed via core.scoring from platform data only.

Category-aware (Structure vs Land):
- Structure rows (Appartement/Maison/Villa/...): total-price stats are
  authoritative; price-per-sqm columns are NULL.
- Land rows (Terrain): price-per-sqm stats are authoritative; total-price
  columns are NULL. Lands are compared by XAF/m2, not total XAF.
- All-types rows (property_type NULL): pooled, kept for trending/cross-type
  signals. `category` is NULL.
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
# Property-type categorization (single source of truth)
# --------------------------------------------------------------------------- #
LAND_TYPES = {"Terrain"}
STRUCTURE_TYPES = {
    "Appartement", "Studio", "Maison", "Villa", "Duplex", "Bungalow",
    "Chambre", "Bureau", "Autre",
}


def category_of(property_type: str | None) -> str | None:
    """Map a raw property_type to a comparison category.

    Returns:
        "Land"      for terrain (compared by XAF/m2)
        "Structure" for buildings (compared by total XAF)
        None        for unknown / NULL types (pooled rows)
    """
    if property_type is None:
        return None
    if property_type in LAND_TYPES:
        return "Land"
    # Anything not explicitly a land type is treated as a structure so new
    # building types (e.g. "Entrepot") still get total-price comparison.
    return "Structure"


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
    # Exclude deactivated listings — garbage/superseded rows (e.g. a Terrain
    # at 6,500 XAF with is_active=False) must not pollute price analytics.
    q = q.filter(CanonicalProperty.is_active == True)
    # Exclude rentals from sale-price analytics so monthly rents (e.g. a
    # studio at 15,000 XAF/month) don't drag down sale-price averages.
    q = q.filter((CanonicalProperty.listing_purpose != "rent"))
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

    `city_median_price` is the median price across the whole city FOR THE SAME
    property_type (or all types when property_type is None), used for the
    premium score normalization.

    Category-aware output:
      - Structure rows: total-price columns populated, price-per-sqm cols NULL.
      - Land rows: price-per-sqm columns populated, total-price cols NULL.
      - All-types row (property_type None): pooled, all columns populated
        (legacy behavior for trending).
    """
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

    # Top-decile share within the city (same-type if property_type given).
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

    category = category_of(property_type)

    # Category-aware column population.
    if category == "Land":
        # Lands: compare by XAF/m2. Total-price columns are NULL.
        if sqm_prices:
            min_sqm = min(sqm_prices)
            max_sqm = max(sqm_prices)
            avg_sqm = statistics.mean(sqm_prices)
        else:
            min_sqm = max_sqm = avg_sqm = None
        return {
            "location_id": location.id,
            "property_type": property_type,
            "category": category,
            "period": "current",
            "listing_count": len(prices),
            "average_price": None,
            "median_price": None,
            "min_price": None,
            "max_price": None,
            "price_per_sqm": round(avg_sqm, 2) if avg_sqm is not None else None,
            "min_price_per_sqm": round(min_sqm, 2) if min_sqm is not None else None,
            "max_price_per_sqm": round(max_sqm, 2) if max_sqm is not None else None,
            "avg_price_per_sqm": round(avg_sqm, 2) if avg_sqm is not None else None,
            "premium_score": prem,
            "demand_score": dem,
            "growth_score": gro,
            "activity_score": act,
            "luxury_score": lux,
            "trend_direction": ("up" if (trend or 0) > 1 else "down" if (trend or 0) < -1 else "flat"),
            "trend_pct": round(trend, 2) if trend is not None else None,
        }

    if category == "Structure":
        # Structures: compare by total XAF. price-per-sqm cols are NULL.
        # Internally compute sqm price for luxury signal context if needed —
        # but per spec we hide it from the DB column.
        return {
            "location_id": location.id,
            "property_type": property_type,
            "category": category,
            "period": "current",
            "listing_count": len(prices),
            "average_price": int(avg),
            "median_price": None,  # user wants median hidden for structures
            "min_price": int(pmin),
            "max_price": int(pmax),
            "price_per_sqm": None,
            "min_price_per_sqm": None,
            "max_price_per_sqm": None,
            "avg_price_per_sqm": None,
            "premium_score": prem,
            "demand_score": dem,
            "growth_score": gro,
            "activity_score": act,
            "luxury_score": lux,
            "trend_direction": ("up" if (trend or 0) > 1 else "down" if (trend or 0) < -1 else "flat"),
            "trend_pct": round(trend, 2) if trend is not None else None,
        }

    # All-types pooled row (property_type NULL, category NULL): keep legacy
    # behavior so trending/cross-type signals still work.
    return {
        "location_id": location.id,
        "property_type": property_type,
        "category": None,
        "period": "current",
        "listing_count": len(prices),
        "average_price": int(avg),
        "median_price": int(median),
        "min_price": int(pmin),
        "max_price": int(pmax),
        "price_per_sqm": round(price_per_sqm, 2) if price_per_sqm else None,
        "min_price_per_sqm": None,
        "max_price_per_sqm": None,
        "avg_price_per_sqm": None,
        "premium_score": prem,
        "demand_score": dem,
        "growth_score": gro,
        "activity_score": act,
        "luxury_score": lux,
        "trend_direction": ("up" if (trend or 0) > 1 else "down" if (trend or 0) < -1 else "flat"),
        "trend_pct": round(trend, 2) if trend is not None else None,
    }


# --------------------------------------------------------------------------- #
# City median helper (category-aware)
# --------------------------------------------------------------------------- #
def _city_median_price(db: Session, city: str,
                       property_type: str | None = None) -> Optional[float]:
    """Median current_best_price across a city, optionally filtered to a
    single property_type. Used for premium_score normalization so a
    neighborhood's premium is measured against the SAME type's city median,
    not the pooled one."""
    q = db.query(CanonicalProperty.current_best_price).join(
        Location, CanonicalProperty.location_id == Location.id
    ).filter(
        Location.city == city,
        CanonicalProperty.current_best_price.isnot(None),
        (CanonicalProperty.listing_purpose != "rent"),
    )
    if property_type:
        q = q.filter(CanonicalProperty.property_type == property_type)
    rows = q.all()
    prices = sorted([r[0] for r in rows if r[0] and r[0] > 0])
    return statistics.median(prices) if prices else None


# --------------------------------------------------------------------------- #
# Full recompute
# --------------------------------------------------------------------------- #
def recompute_all(db: Session) -> dict:
    """Recompute analytics for every location and write to the
    neighborhood_analytics cache. Returns a stats dict.

    Stale rows from previous runs (e.g. locations that no longer have enough
    listings, or property types that have been deactivated) are deleted
    up-front so the cache always reflects the current data.
    """
    stats = {"locations": 0, "rows_written": 0, "skipped": 0}
    # Clear stale rows — without this, locations whose listings have been
    # deactivated/removed would keep their old analytics forever.
    db.query(NeighborhoodAnalytics).delete()
    db.commit()
    locations = db.query(Location).all()
    # Precompute city medians per (city, property_type) for premium-score
    # normalization. The None key holds the all-types median.
    city_medians: dict[tuple[str, str | None], Optional[float]] = {}
    for loc in locations:
        if (loc.city, None) not in city_medians:
            city_medians[(loc.city, None)] = _city_median_price(db, loc.city, None)
        # Collect the distinct types present in this city.
        types_in_city = {
            c.property_type for c in
            db.query(CanonicalProperty).join(Location,
                     CanonicalProperty.location_id == Location.id)
            .filter(Location.city == loc.city,
                    CanonicalProperty.current_best_price.isnot(None)).all()
            if c.property_type
        }
        for ptype in types_in_city:
            if (loc.city, ptype) not in city_medians:
                city_medians[(loc.city, ptype)] = _city_median_price(db, loc.city, ptype)

    for loc in locations:
        stats["locations"] += 1
        # All-types row (property_type NULL) + per-type rows.
        seen_types = {c.property_type for c in _location_canonicals(db, loc, None)}
        for ptype in [None, *sorted(t for t in seen_types if t)]:
            row = compute_for_location(
                db, loc,
                city_medians.get((loc.city, ptype)),
                ptype,
            )
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
def _city_level_analytics(db: Session, city: str,
                          property_type: str | None) -> NeighborhoodAnalytics | None:
    """Aggregate analytics at the city level for a given property_type.

    Used as a geographic fallback when a neighborhood's row for a type has
    fewer than 3 listings. Computes stats directly from canonical_properties
    in that city for that type. Returns a transient (non-persisted)
    NeighborhoodAnalytics-like object with a synthetic location_id of None.
    """
    canons = (
        db.query(CanonicalProperty)
        .join(Location, CanonicalProperty.location_id == Location.id)
        .filter(
            Location.city == city,
            CanonicalProperty.current_best_price.isnot(None),
            CanonicalProperty.current_best_price > 0,
        )
    )
    if property_type:
        canons = canons.filter(CanonicalProperty.property_type == property_type)
    canons = canons.all()
    if not canons:
        return None

    prices = sorted([c.current_best_price for c in canons if c.current_best_price])
    category = category_of(property_type)
    sqm_prices = [c.current_best_price / c.area_sqm for c in canons
                  if c.area_sqm and c.area_sqm > 0 and c.current_best_price]

    row = NeighborhoodAnalytics()
    row.location_id = None
    row.property_type = property_type
    row.category = category
    row.period = "current"
    row.listing_count = len(prices)
    row.computed_at = datetime.now(timezone.utc)

    if category == "Land":
        row.average_price = None
        row.median_price = None
        row.min_price = None
        row.max_price = None
        row.price_per_sqm = round(statistics.mean(sqm_prices), 2) if sqm_prices else None
        row.min_price_per_sqm = round(min(sqm_prices), 2) if sqm_prices else None
        row.max_price_per_sqm = round(max(sqm_prices), 2) if sqm_prices else None
        row.avg_price_per_sqm = round(statistics.mean(sqm_prices), 2) if sqm_prices else None
    elif category == "Structure":
        row.average_price = int(statistics.mean(prices))
        row.median_price = None
        row.min_price = int(prices[0])
        row.max_price = int(prices[-1])
        row.price_per_sqm = None
        row.min_price_per_sqm = None
        row.max_price_per_sqm = None
        row.avg_price_per_sqm = None
    else:  # all-types pooled
        row.average_price = int(statistics.mean(prices))
        row.median_price = int(statistics.median(prices))
        row.min_price = int(prices[0])
        row.max_price = int(prices[-1])
        row.price_per_sqm = round(statistics.mean(sqm_prices), 2) if sqm_prices else None
        row.min_price_per_sqm = None
        row.max_price_per_sqm = None
        row.avg_price_per_sqm = None
    return row


def get_location_analytics(db: Session, location_id: int,
                           property_type: str | None = None
                           ) -> NeighborhoodAnalytics | None:
    """Return analytics for a location + property_type with a geographic
    fallback to the city-level aggregate when the neighborhood row has
    fewer than 3 listings.

    The returned object has a transient `fallback_level` attribute set to
    "neighborhood" or "city" (None if no data at all).
    """
    row = db.query(NeighborhoodAnalytics).filter(
        NeighborhoodAnalytics.location_id == location_id,
        NeighborhoodAnalytics.property_type == property_type,
        NeighborhoodAnalytics.period == "current",
    ).first()

    if row is not None and row.listing_count is not None and row.listing_count >= 3:
        row.fallback_level = "neighborhood"
        return row

    # Insufficient neighborhood data — try city-level aggregate.
    loc = db.query(Location).filter(Location.id == location_id).first()
    if loc is None:
        return None
    city_row = _city_level_analytics(db, loc.city, property_type)
    if city_row is None:
        return None
    city_row.fallback_level = "city"
    return city_row


def find_location_by_slug(db: Session, slug: str) -> Location | None:
    return db.query(Location).filter(Location.slug == slug).first()


# --------------------------------------------------------------------------- #
# Shared price-analysis helper (used by api/annonces + api/chat)
# --------------------------------------------------------------------------- #
def compute_price_analysis(db: Session, canon: CanonicalProperty) -> dict:
    """Category-aware market position analysis for a canonical property.

    Returns a dict matching the PriceAnalyse schema plus a few internal keys.
    Comparison logic:
      - Structure (Appartement/Maison/...): compare total price vs the mean
        total price of same-type comparables in the same city. Verdict bands
        are ±10% on the total-price delta.
      - Land (Terrain): compare listing price/area_sqm vs the mean
        price/area_sqm of land comparables in the same city. Verdict bands
        are ±10% on the XAF/m2 delta.
    Geographic fallback: if the property's neighborhood has fewer than 3
    same-type comparables, the comparison set is widened to the whole city
    (fallback_level="city"); otherwise fallback_level="neighborhood".
    """
    price = canon.current_best_price
    city = canon.location.city if canon.location else None
    ptype = canon.property_type
    category = category_of(ptype)
    area = canon.area_sqm

    base = {
        "listing_id": canon.id,
        "price": price,
        "city": city,
        "property_type": ptype,
        "category": category,
        "comparison_metric": None,
        "sample_size": 0,
        "min_price": None, "max_price": None,
        "mean_price": None, "median_price": None,
        "min_price_per_sqm": None, "max_price_per_sqm": None,
        "avg_price_per_sqm": None,
        "avg_comparison": None,
        "listing_comparison": None,
        "savings": None,
        "percentile": None,
        "verdict": "insufficient_data",
        "summary": "",
        "fallback_level": None,
    }

    if price is None or not city or not ptype:
        base["summary"] = "Donnees insuffisantes pour analyser ce bien."
        return base

    if category == "Land" and (not area or area <= 0):
        base["summary"] = (
            "Surface non renseignee pour ce terrain — comparaison au m2 impossible."
        )
        return base

    # --- Gather comparables (same type, same city, exclude self) ---------
    # First try same neighborhood; fall back to whole city if < 3.
    neighborhood_filter = None
    if canon.location and canon.location.neighborhood:
        neighborhood_filter = canon.location.neighborhood

    def _fetch_comparables(neigh_filter: str | None):
        q = (
            db.query(CanonicalProperty)
            .join(Location, CanonicalProperty.location_id == Location.id)
            .filter(
                CanonicalProperty.property_type == ptype,
                Location.city == city,
                CanonicalProperty.current_best_price.isnot(None),
                CanonicalProperty.current_best_price > 0,
                CanonicalProperty.is_active == True,
                CanonicalProperty.id != canon.id,
                # Keep rentals out of sale-price comparables.
                (CanonicalProperty.listing_purpose != "rent"),
            )
        )
        if neigh_filter is not None:
            q = q.filter(Location.neighborhood == neigh_filter)
        return q.all()

    comparables = _fetch_comparables(neighborhood_filter) if neighborhood_filter else []
    fallback_level = "neighborhood"
    if len(comparables) < 2:  # need at least 2 comparables (+ self = 3 sample)
        comparables = _fetch_comparables(None)
        fallback_level = "city"

    if not comparables:
        base["fallback_level"] = fallback_level
        base["summary"] = (
            f"Pas encore assez de {ptype.lower()}s a {city} pour comparer."
        )
        return base

    # --- Category-specific comparison -----------------------------------
    if category == "Land":
        # Lands: compare XAF/m2.
        listing_psm = price / area
        comp_psm = [c.current_best_price / c.area_sqm
                    for c in comparables
                    if c.area_sqm and c.area_sqm > 0 and c.current_best_price]
        if not comp_psm:
            base["fallback_level"] = fallback_level
            base["summary"] = (
                f"Aucun terrain comparable avec surface connue a {city}."
            )
            return base
        sample = sorted(comp_psm + [listing_psm])
        sample_size = len(sample)
        avg_psm = statistics.mean(comp_psm)
        min_psm = min(comp_psm)
        max_psm = max(comp_psm)
        savings = avg_psm - listing_psm  # positive = below market
        below = sum(1 for p in comp_psm if p <= listing_psm)
        percentile = round(100.0 * below / len(comp_psm), 1)
        # Verdict bands on XAF/m2 delta vs comparables mean.
        if avg_psm > 0:
            delta_pct = ((listing_psm - avg_psm) / avg_psm) * 100
        else:
            delta_pct = 0.0
        if delta_pct <= -10:
            verdict = "below_market"
        elif delta_pct >= 10:
            verdict = "above_market"
        else:
            verdict = "around_market"

        if verdict == "below_market":
            phrase = f"Ce terrain est en dessous du marche."
            economy = f"Vous economisez {abs(int(savings)):,} XAF/m2 par rapport au prix moyen au m2."
        elif verdict == "above_market":
            phrase = f"Ce terrain est au-dessus du marche."
            economy = f"Vous payez plus de {abs(int(savings)):,} XAF/m2 par rapport au prix moyen au m2."
        else:
            phrase = f"Ce terrain est dans la moyenne du marche."
            economy = f"Prix au m2 dans la fourchette moyenne (±10%)."
        summary = (
            f"{phrase} {economy} "
            f"Base sur {len(comp_psm)} terrain(s) comparable(s) "
            f"(moyenne {int(avg_psm):,} XAF/m2)."
        ).replace(",", " ")

        base.update({
            "comparison_metric": "price_per_sqm",
            "sample_size": sample_size,
            "min_price_per_sqm": round(min_psm, 2),
            "max_price_per_sqm": round(max_psm, 2),
            "avg_price_per_sqm": round(avg_psm, 2),
            "avg_comparison": round(avg_psm, 2),
            "listing_comparison": round(listing_psm, 2),
            "savings": round(savings, 2),
            "percentile": percentile,
            "verdict": verdict,
            "summary": summary,
            "fallback_level": fallback_level,
        })
        return base

    # Structure: compare total price.
    comp_prices = [c.current_best_price for c in comparables
                   if c.current_best_price and c.current_best_price > 0]
    sample = sorted(comp_prices + [price])
    sample_size = len(sample)
    if sample_size < 3:
        base["fallback_level"] = fallback_level
        base["summary"] = (
            f"Pas encore assez de {ptype.lower()}s a {city} pour comparer "
            f"({len(comp_prices)} bien(s) similaire(s))."
        )
        return base

    avg_price = statistics.mean(comp_prices)
    min_price = min(comp_prices)
    max_price = max(comp_prices)
    median_price = int(statistics.median(sample))
    savings = avg_price - price  # positive = below market
    below = sum(1 for p in comp_prices if p <= price)
    percentile = round(100.0 * below / len(comp_prices), 1)
    if avg_price > 0:
        delta_pct = ((price - avg_price) / avg_price) * 100
    else:
        delta_pct = 0.0
    if delta_pct <= -10:
        verdict = "below_market"
    elif delta_pct >= 10:
        verdict = "above_market"
    else:
        verdict = "around_market"

    if verdict == "below_market":
        phrase = f"Ce bien est en dessous du marche."
        economy = f"Vous economisez {abs(int(savings)):,} XAF par rapport au prix moyen."
    elif verdict == "above_market":
        phrase = f"Ce bien est au-dessus du marche."
        economy = f"Vous payez plus de {abs(int(savings)):,} XAF par rapport au prix moyen."
    else:
        phrase = f"Ce bien est dans la moyenne du marche."
        economy = f"Prix dans la fourchette moyenne (±10%)."
    summary = (
        f"{phrase} {economy} "
        f"Base sur {len(comp_prices)} bien(s) similaire(s) "
        f"(moyenne {int(avg_price):,} XAF)."
    ).replace(",", " ")

    base.update({
        "comparison_metric": "total_price",
        "sample_size": sample_size,
        "min_price": int(min_price),
        "max_price": int(max_price),
        "mean_price": int(avg_price),
        "median_price": median_price,
        "avg_comparison": round(float(avg_price), 2),
        "listing_comparison": round(float(price), 2),
        "savings": round(float(savings), 2),
        "percentile": percentile,
        "verdict": verdict,
        "summary": summary,
        "fallback_level": fallback_level,
    })
    return base