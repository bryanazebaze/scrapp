"""Listing endpoints — server-side filtered, paginated, with detail + history."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

_TRACKING_HOSTS = (
    "facebook.com/tr", "facebook.net", "googletagmanager.com",
    "google-analytics.com", "doubleclick.net", "hotjar.com", "clarity.ms",
    "scorecardresearch", "quantserve.com",
)


def _is_tracking(url: str) -> bool:
    low = url.lower()
    return any(tok in low for tok in _TRACKING_HOSTS)


def _localized_description(best_raw: RawListing, lang: str, db: Session) -> str | None:
    """Return the listing description in the requested language.

    raw_listings.description_raw is the immutable French original. When
    lang == 'en', look up an English translation in listing_translations;
    fall back to the French original if none exists (e.g. not yet translated).
    """
    if lang == "en" and best_raw.description_raw:
        tr = db.query(ListingTranslation).filter(
            ListingTranslation.raw_listing_id == best_raw.id,
            ListingTranslation.language == "en",
        ).first()
        if tr and tr.description:
            return tr.description
    return best_raw.description_raw

from core.database import get_db
from core.i18n import preferred_lang
from core.models import (
    CanonicalProperty, RawListing, ListingHistory, ListingTranslation, Location, Source,
)
from core.schemas import (
    AnnonceBreve, AnnonceDetaillee, ListingHistoryEvent, RawListingBrief,
    PriceAnalyse,
)

router = APIRouter(prefix="/annonces", tags=["listings"])


def _canon_to_breve(c: CanonicalProperty, loc: Location | None,
                     best_raw: RawListing | None) -> AnnonceBreve:
    images = []
    if best_raw and best_raw.images_raw:
        images = [u for u in best_raw.images_raw
                  if isinstance(u, str) and not _is_tracking(u)][:8]
    return AnnonceBreve(
        id=c.id,
        title=c.title_canonical,
        property_type=c.property_type,
        price=c.current_best_price,
        currency="XAF",
        city=loc.city if loc else None,
        neighborhood=loc.neighborhood if loc else None,
        location_slug=loc.slug if loc else None,
        lat=loc.lat if loc else None,
        lng=loc.lng if loc else None,
        bedrooms=c.bedrooms,
        bathrooms=c.bathrooms,
        area_sqm=c.area_sqm,
        images=images,
        best_source=best_raw.source.slug if best_raw and best_raw.source else None,
    )


@router.get("", response_model=List[AnnonceBreve])
def list_annonces(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    neighborhood: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    min_bathrooms: Optional[int] = None,
    q: Optional[str] = Query(None, description="Text search on title"),
    db: Session = Depends(get_db),
):
    """Paginated listings with server-side filtering.

    City and neighborhood use case-insensitive partial matching (ILIKE),
    so 'bonamoussadi' matches 'Bonamoussadi' and 'bona' also matches.
    The `q` param does a text search on the canonical title and the
    description of linked raw listings (ILIKE, case-insensitive).
    """
    query = db.query(CanonicalProperty).filter(
        CanonicalProperty.is_active == True,
        CanonicalProperty.current_best_price.isnot(None),
    )
    if property_type:
        query = query.filter(CanonicalProperty.property_type == property_type)
    if q:
        # Search title on canonical + description on any linked raw listing
        desc_exists = (
            db.query(RawListing.id)
            .filter(
                RawListing.canonical_property_id == CanonicalProperty.id,
                RawListing.description_raw.ilike(f"%{q}%"),
            )
            .exists()
        )
        query = query.filter(
            CanonicalProperty.title_canonical.ilike(f"%{q}%") | desc_exists
        )
    if city or neighborhood:
        query = query.join(Location, CanonicalProperty.location_id == Location.id)
        if city:
            # "Ville ou Quartier" — match against both city and neighborhood
            query = query.filter(
                Location.city.ilike(f"%{city}%")
                | Location.neighborhood.ilike(f"%{city}%")
            )
        if neighborhood:
            query = query.filter(Location.neighborhood.ilike(f"%{neighborhood}%"))
    if min_price is not None:
        query = query.filter(CanonicalProperty.current_best_price >= min_price)
    if max_price is not None:
        query = query.filter(CanonicalProperty.current_best_price <= max_price)
    if min_bedrooms is not None:
        query = query.filter(CanonicalProperty.bedrooms >= min_bedrooms)
    if max_bedrooms is not None:
        query = query.filter(CanonicalProperty.bedrooms <= max_bedrooms)
    if min_area is not None:
        query = query.filter(CanonicalProperty.area_sqm >= min_area)
    if max_area is not None:
        query = query.filter(CanonicalProperty.area_sqm <= max_area)
    if min_bathrooms is not None:
        query = query.filter(CanonicalProperty.bathrooms >= min_bathrooms)

    canons = query.order_by(CanonicalProperty.last_seen_at.desc()) \
              .offset(skip).limit(limit).all()
    results = []
    for c in canons:
        loc = c.location
        best = db.query(RawListing).filter(
            RawListing.canonical_property_id == c.id,
            RawListing.price_parsed == c.current_best_price,
        ).first()
        results.append(_canon_to_breve(c, loc, best))
    return results


@router.get("/nearby", response_model=List[AnnonceBreve])
def get_nearby_annonces(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(5.0),
    db: Session = Depends(get_db)
):
    import math
    def haversine(lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None: return float('inf')
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    query = db.query(CanonicalProperty).join(Location, CanonicalProperty.location_id == Location.id).filter(
        CanonicalProperty.is_active == True,
        CanonicalProperty.current_best_price.isnot(None),
        Location.lat.isnot(None),
        Location.lng.isnot(None)
    ).all()

    nearby_canons = []
    for c in query:
        dist = haversine(lat, lng, c.location.lat, c.location.lng)
        if dist <= radius_km:
            nearby_canons.append((dist, c))
    
    nearby_canons.sort(key=lambda x: x[0])
    
    results = []
    for dist, c in nearby_canons[:50]:
        best = db.query(RawListing).filter(
            RawListing.canonical_property_id == c.id,
            RawListing.price_parsed == c.current_best_price,
        ).first()
        breve = _canon_to_breve(c, c.location, best)
        # Optional: could override location_slug or create a distance field, but distance will be calculated client side
        results.append(breve)
    return results


@router.get("/{annonce_id}", response_model=AnnonceDetaillee)
def get_annonce(annonce_id: int, request: Request, db: Session = Depends(get_db)):
    lang = preferred_lang(request)
    canon = db.query(CanonicalProperty).filter(
        CanonicalProperty.id == annonce_id
    ).first()
    if not canon:
        raise HTTPException(404, "Annonce non trouvée")

    raws = db.query(RawListing).filter(
        RawListing.canonical_property_id == canon.id
    ).all()
    # Sort by price ascending (cheapest first)
    raws.sort(key=lambda r: r.price_parsed or float('inf'))

    sources = []
    best_raw = raws[0] if raws else None
    for r in raws:
        src = db.query(Source).filter(Source.id == r.source_id).first()
        sources.append(RawListingBrief(
            id=r.id,
            source_slug=src.slug if src else None,
            source_display_name=src.display_name if src else None,
            url_source=r.url_source,
            price_parsed=r.price_parsed,
            currency=r.currency,
            review_status=r.review_status,
            match_confidence=r.match_confidence,
        ))

    history = db.query(ListingHistory).filter(
        ListingHistory.canonical_property_id == canon.id
    ).order_by(ListingHistory.observed_at.asc()).all()

    images = []
    if best_raw and best_raw.images_raw:
        images = [u for u in best_raw.images_raw
              if isinstance(u, str) and not _is_tracking(u)][:8]

    return AnnonceDetaillee(
        id=canon.id,
        title=canon.title_canonical,
        property_type=canon.property_type,
        price=canon.current_best_price,
        currency="XAF",
        city=canon.location.city if canon.location else None,
        neighborhood=canon.location.neighborhood if canon.location else None,
        location_slug=canon.location.slug if canon.location else None,
        bedrooms=canon.bedrooms,
        bathrooms=canon.bathrooms,
        area_sqm=canon.area_sqm,
        images=images,
        best_source=best_raw.source.slug if best_raw and best_raw.source else None,
        description=_localized_description(best_raw, lang, db) if best_raw else None,
        location_raw=best_raw.location_raw if best_raw else None,
        sources=sources,
        price_history=[ListingHistoryEvent.model_validate(h) for h in history],
        match_explanation=best_raw.match_explanation if best_raw else None,
        match_confidence=best_raw.match_confidence if best_raw else None,
        created_at=canon.created_at,
        last_seen_at=canon.last_seen_at,
    )


@router.get("/{annonce_id}/history", response_model=List[ListingHistoryEvent])
def get_annonce_history(annonce_id: int, db: Session = Depends(get_db)):
    """Price/availability timeline for a canonical property."""
    canon = db.query(CanonicalProperty).filter(
        CanonicalProperty.id == annonce_id
    ).first()
    if not canon:
        raise HTTPException(404, "Annonce non trouvée")
    events = db.query(ListingHistory).filter(
        ListingHistory.canonical_property_id == canon.id
    ).order_by(ListingHistory.observed_at.asc()).all()
    return [ListingHistoryEvent.model_validate(e) for e in events]


@router.get("/{annonce_id}/similar", response_model=List[AnnonceBreve])
def get_similar_annonces(annonce_id: int, db: Session = Depends(get_db)):
    """Return up to 10 similar properties.

    Matches same `property_type` AND same `location_id` first. If fewer
    than 5 same-location matches are found, broadens to same city + same
    property_type. Excludes the property itself. Ordered by last_seen desc.
    """
    canon = db.query(CanonicalProperty).filter(
        CanonicalProperty.id == annonce_id
    ).first()
    if not canon:
        raise HTTPException(404, "Annonce non trouvée")

    ptype = canon.property_type
    loc_id = canon.location_id

    def _build_results(canons):
        out = []
        for c in canons:
            best = db.query(RawListing).filter(
                RawListing.canonical_property_id == c.id,
                RawListing.price_parsed == c.current_best_price,
            ).first()
            out.append(_canon_to_breve(c, c.location, best))
        return out

    base_filter = [
        CanonicalProperty.is_active == True,
        CanonicalProperty.current_best_price.isnot(None),
        CanonicalProperty.id != canon.id,
        CanonicalProperty.property_type == ptype,
    ]

    # Try exact location match first.
    canons = []
    if loc_id is not None:
        canons = (
            db.query(CanonicalProperty)
            .filter(*base_filter, CanonicalProperty.location_id == loc_id)
            .order_by(CanonicalProperty.last_seen_at.desc())
            .limit(10)
            .all()
        )

    # Broaden to same city if too few exact-location matches.
    if len(canons) < 5 and canon.location:
        city = canon.location.city
        already_ids = {c.id for c in canons}
        already_ids.add(canon.id)
        broad = (
            db.query(CanonicalProperty)
            .join(Location, CanonicalProperty.location_id == Location.id)
            .filter(*base_filter, Location.city == city)
            .filter(CanonicalProperty.id.notin_(already_ids))
            .order_by(CanonicalProperty.last_seen_at.desc())
            .limit(10 - len(canons))
            .all()
        )
        canons.extend(broad)

    return _build_results(canons[:10])


@router.get("/{annonce_id}/analyse", response_model=PriceAnalyse)
def analyse_prix(annonce_id: int, db: Session = Depends(get_db)):
    """Compare a property's price against comparable listings
    (same property_type + same city) and return a market-position verdict.

    Uses the normalized `locations` table (no hardcoded city list). Falls
    back to "insufficient_data" when fewer than 3 comparables are available.
    """
    canon = db.query(CanonicalProperty).filter(
        CanonicalProperty.id == annonce_id
    ).first()
    if not canon:
        raise HTTPException(404, "Annonce non trouvée")

    price = canon.current_best_price
    city = canon.location.city if canon.location else None
    ptype = canon.property_type

    # Base response (insufficient-data shape)
    base = PriceAnalyse(
        listing_id=canon.id,
        price=price,
        city=city,
        property_type=ptype,
        sample_size=0,
        min_price=None, max_price=None,
        mean_price=None, median_price=None,
        percentile=None,
        verdict="insufficient_data",
        summary="",
    )

    if price is None or not city or not ptype:
        base.summary = "Données insuffisantes pour analyser ce bien."
        return base

    # Comparables: same type + same city, with a price, excluding this listing.
    comparables = (
        db.query(CanonicalProperty.current_best_price)
        .join(Location, CanonicalProperty.location_id == Location.id)
        .filter(
            CanonicalProperty.property_type == ptype,
            Location.city == city,
            CanonicalProperty.current_best_price.isnot(None),
            CanonicalProperty.is_active == True,
            CanonicalProperty.id != canon.id,
        )
        .all()
    )
    prices = sorted([r[0] for r in comparables if r[0] is not None])

    # Include this listing in the distribution for percentile calc.
    sample = sorted(prices + [price])
    sample_size = len(sample)

    if sample_size < 3:
        base.summary = (
            f"Pas encore assez de {ptype.lower()}s à {city} pour comparer "
            f"({sample_size - 1} bien(s) similaire(s))."
        )
        return base

    import statistics
    mean_price = int(statistics.mean(sample))
    median_price = int(statistics.median(sample))
    min_price = sample[0]
    max_price = sample[-1]

    # Percentile: fraction of sample at or below this price (0-100).
    below = sum(1 for p in prices if p <= price)
    percentile = round(100.0 * below / len(prices), 1)

    # Verdict bands (relative to median).
    delta_pct = ((price - median_price) / median_price * 100) if median_price else 0
    if delta_pct <= -10:
        verdict = "below_market"
    elif delta_pct >= 10:
        verdict = "above_market"
    else:
        verdict = "around_market"

    verdict_phrases = {
        "below_market": f"{abs(delta_pct):.0f}% sous le prix médian des {ptype.lower()}s à {city}.",
        "around_market": f"Prix dans la moyenne des {ptype.lower()}s à {city} (±10%).",
        "above_market": f"{delta_pct:.0f}% au-dessus du prix médian des {ptype.lower()}s à {city}.",
    }
    summary = (
        f"{verdict_phrases[verdict]} "
        f"Basé sur {len(prices)} bien(s) similaire(s) "
        f"(médiane {median_price:,} XAF)."
    ).replace(",", " ")

    return PriceAnalyse(
        listing_id=canon.id,
        price=price,
        city=city,
        property_type=ptype,
        sample_size=sample_size,
        min_price=min_price,
        max_price=max_price,
        mean_price=mean_price,
        median_price=median_price,
        percentile=percentile,
        verdict=verdict,
        summary=summary,
    )