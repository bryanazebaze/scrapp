"""Ingest pipeline — turns RawListingDrafts into raw_listings + canonical
properties + listing_history.

This replaces the legacy `fusionner_ou_inserer` (core/fusion.py:70). The old
function overwrote `meilleur_prix` (fusion.py:97) — destroying price history —
and used a full-table +/-15% price scan for dedup that doesn't scale.

New flow (per draft):
1. Idempotent insert: url_hash = sha256(url_source). If a raw_listing with
   that hash already exists, this is a RE-CRAWL — fetch the existing row,
   compare the fresh price/availability to the latest listing_history event,
   and append a price_change/availability_change event only if something
   moved. Update canonical.last_seen_at. (No new raw_listing row.)
2. New URL: resolve a location_id from location_raw, run the matcher
   (match_key lookup + composite DCS), and either link to an existing
   canonical property or create a new one. Append a `first_seen` history
   event.
3. Universal-scraper gating: drafts with confidence < 0.40 are rejected at
   ingest; 0.40-0.74 stay `pending` for human review (canonical_property_id
   NULL); >= 0.75 (or any dedicated-source draft) auto-promote.

Post-crawl cleanup (mark_removed) is called separately by the scheduler:
any raw_listing whose latest crawl_session_id != the current one is marked
`removed` (an availability_change event), so disappearances are tracked
without re-scanning the whole table.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from core.models import (
    RawListing, CanonicalProperty, Location, ListingHistory, Source,
)
from scrapers.drafts import RawListingDraft
from scrapers.utils import (
    normalize_text, slugify, detect_city, detect_neighborhood,
    infer_city_from_neighborhood, neighborhood_coords, normalize_url,
)
from .matcher import (
    find_canonical_match, compute_match_key, explanation_dict, MatchResult,
)


# --------------------------------------------------------------------------- #
# Location resolution
# --------------------------------------------------------------------------- #
def resolve_location(db: Session, location_raw: str | None) -> int | None:
    """Resolve a raw location string to a locations.id, creating the row if
    needed. Returns None if no city can be parsed (the locations table requires
    city NOT NULL, so we skip creating a row when city is missing).

    City resolution tries three strategies in order:
    1. detect_city — a known city name appears in the text.
    2. infer_city_from_neighborhood — a known neighborhood appears and its
       city is inferred from the neighborhood→city mapping.
    3. Give up (return None).
    Coordinates are populated from the neighborhood coords table when available.
    """
    if not location_raw:
        return None
    city = detect_city(location_raw)
    neighborhood = detect_neighborhood(location_raw, city)
    if not city and neighborhood:
        city = infer_city_from_neighborhood(neighborhood)
    if not city:
        return None
    # Check by slug (unique constraint) to catch case where the city/neighborhood
    # strings differ slightly but slugify to the same slug.
    slug = slugify("-".join(filter(None, [city, neighborhood]))) or "unknown"
    existing = db.query(Location).filter(Location.slug == slug).first()
    if existing:
        # Backfill lat/lng if we now have coords and the existing row doesn't.
        if existing.lat is None or existing.lng is None:
            lat, lng = neighborhood_coords(neighborhood, city)
            if lat is not None:
                existing.lat = lat
                existing.lng = lng
        return existing.id
    # Also check by exact city+neighborhood match (covers case where slug differs).
    existing = db.query(Location).filter(
        Location.city == city,
        func.coalesce(Location.neighborhood, "") == (neighborhood or ""),
    ).first()
    if existing:
        return existing.id
    lat, lng = neighborhood_coords(neighborhood, city)
    loc = Location(city=city, neighborhood=neighborhood, slug=slug,
                   lat=lat, lng=lng)
    db.add(loc)
    try:
        db.flush()
    except Exception:
        # Race: another thread/row created the same slug. Re-query.
        db.rollback()
        existing = db.query(Location).filter(Location.slug == slug).first()
        if existing:
            return existing.id
        return None
    return loc.id


# --------------------------------------------------------------------------- #
# Canonical property creation
# --------------------------------------------------------------------------- #
def create_canonical(db: Session, draft: RawListingDraft,
                     location_id: int | None) -> CanonicalProperty:
    city = detect_city(draft.location_raw)
    neighborhood = detect_neighborhood(draft.location_raw, city)
    mk = compute_match_key(draft.property_type_raw, city, neighborhood)
    if mk is None:
        # No city parsed — synthesize a unique key so the property is still
        # stored; it just won't be key-matchable against future listings.
        mk = "noloc:" + hashlib.sha1(draft.url_source.encode("utf-8")).hexdigest()
    # Sanity-cap bedrooms/bathrooms to smallint range (max 32767).
    # Scrapers may extract wrong values (e.g. surface area parsed as bathrooms).
    bedrooms = draft.bedrooms
    # A "Chambre" listing IS one room, so its bedroom count must be +1.
    if draft.property_type_raw == "Chambre":
        bedrooms = (bedrooms or 0) + 1
    if bedrooms is not None and (bedrooms < 0 or bedrooms > 50):
        bedrooms = None
    bathrooms = draft.bathrooms
    if bathrooms is not None and (bathrooms < 0 or bathrooms > 50):
        bathrooms = None
    # area_sqm: reject 0 and negative — a 0 area is always an extraction
    # failure, not a real value, and it poisons the match_key by collapsing
    # distinct properties that share (type, loc, beds, price) into one bucket.
    area_sqm = draft.area_sqm
    if area_sqm is not None and area_sqm <= 0:
        area_sqm = None
    # Cap price to BigInteger range (max ~9.2×10^18).
    price = draft.price_parsed
    if price is not None and price > 9_000_000_000_000:
        price = None
    canon = CanonicalProperty(
        match_key=mk,
        title_canonical=draft.title_raw,
        title_normalized=normalize_text(draft.title_raw),
        property_type=draft.property_type_raw or "Inconnu",
        location_id=location_id,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        area_sqm=area_sqm,
        current_best_price=price,
        current_availability="available",
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(canon)
    db.flush()
    return canon


# --------------------------------------------------------------------------- #
# History
# --------------------------------------------------------------------------- #
def _latest_event(db: Session, raw_listing_id: int) -> ListingHistory | None:
    return db.query(ListingHistory).filter(
        ListingHistory.raw_listing_id == raw_listing_id
    ).order_by(desc(ListingHistory.observed_at)).first()


def append_history_if_changed(db: Session, raw_listing_id: int,
                               canonical_id: int, price: int | None,
                               availability: str, crawl_session_id) -> None:
    """Compare to the latest event for this raw_listing and append a change
    event only if price or availability moved. No-op if identical."""
    latest = _latest_event(db, raw_listing_id)
    price_changed = (price is not None) and (latest is None or latest.price_observed != price)
    avail_changed = (latest is None) or (latest.availability != availability)
    if not price_changed and not avail_changed:
        return
    diff = {}
    if latest is not None:
        if price_changed:
            diff["old_price"] = latest.price_observed
            diff["new_price"] = price
        if avail_changed:
            diff["old_availability"] = latest.availability
            diff["new_availability"] = availability
    event_type = "price_change" if price_changed and not avail_changed else (
        "availability_change" if avail_changed and not price_changed else "price_change"
    )
    db.add(ListingHistory(
        raw_listing_id=raw_listing_id,
        canonical_property_id=canonical_id,
        event_type=event_type,
        price_observed=price,
        availability=availability,
        crawl_session_id=crawl_session_id,
        diff=diff or None,
    ))


# --------------------------------------------------------------------------- #
# Review-status gating for the universal scraper
# --------------------------------------------------------------------------- #
CONFIDENCE_REJECT = 0.40
CONFIDENCE_AUTO = 0.75


def _review_status_for(adapter_kind: str, confidence: float,
                        match_result: MatchResult) -> str:
    """Dedicated sources auto-promote. Universal sources gate on confidence."""
    if adapter_kind == "dedicated":
        return "auto_promoted"
    if confidence < CONFIDENCE_REJECT:
        return "rejected"
    if confidence >= CONFIDENCE_AUTO or match_result.auto_promote:
        return "auto_promoted"
    return "pending"


# --------------------------------------------------------------------------- #
# Main entry
# --------------------------------------------------------------------------- #
def ingest(db: Session, drafts: Iterable[RawListingDraft], source_id: int,
           crawl_session_id, adapter_kind: str = "dedicated") -> dict:
    """Ingest a batch of drafts from one source. Returns a stats dict."""
    stats = {"new": 0, "recrawl": 0, "rejected": 0, "linked": 0, "created_canonical": 0}
    for draft in drafts:
        url_hash = hashlib.sha256(
            normalize_url(draft.url_source).encode("utf-8")
        ).hexdigest()
        existing = db.query(RawListing).filter(RawListing.url_hash == url_hash).first()

        if existing:
            # RE-CRAWL: update session tracking so mark_removed doesn't flag
            # this listing as disappeared. Compare to latest history and
            # append a change event only if price/availability moved.
            existing.crawl_session_id = crawl_session_id
            existing.crawled_at = datetime.now(timezone.utc)
            canon_id = existing.canonical_property_id
            if canon_id:
                append_history_if_changed(
                    db, existing.id, canon_id, draft.price_parsed,
                    "available", crawl_session_id,
                )
                canon = db.query(CanonicalProperty).filter(
                    CanonicalProperty.id == canon_id).first()
                if canon:
                    canon.last_seen_at = datetime.now(timezone.utc)
                    if draft.price_parsed and (
                        canon.current_best_price is None
                        or draft.price_parsed < canon.current_best_price
                    ):
                        canon.current_best_price = draft.price_parsed
            stats["recrawl"] += 1
            continue

        # NEW listing.
        location_id = resolve_location(db, draft.location_raw)
        match_result = find_canonical_match(db, draft, location_id)
        review_status = _review_status_for(adapter_kind, draft.confidence, match_result)

        if review_status == "rejected":
            stats["rejected"] += 1
            continue

        # Only auto-promoted listings create/link a canonical property. Pending
        # listings sit in raw_listings with canonical_property_id=NULL until a
        # human approves them (POST /admin/review), at which point the
        # canonical is created/linked and a first_seen event is backdated.
        # Sanity-cap price to BigInteger range before insert.
        capped_price = draft.price_parsed
        if capped_price is not None and capped_price > 9_000_000_000_000:
            capped_price = None
        canon_id: int | None = None
        if review_status == "auto_promoted":
            if match_result.auto_promote and match_result.canonical_id:
                canon_id = match_result.canonical_id
                stats["linked"] += 1
            else:
                canon = create_canonical(db, draft, location_id)
                canon_id = canon.id
                stats["created_canonical"] += 1

        raw = RawListing(
            source_id=source_id,
            url_source=draft.url_source,
            url_hash=url_hash,
            title_raw=draft.title_raw,
            price_raw=draft.price_raw,
            price_parsed=capped_price,
            currency=draft.currency,
            location_raw=draft.location_raw,
            description_raw=draft.description_raw,
            property_type_raw=draft.property_type_raw,
            images_raw=draft.images_raw or [],
            payload=draft.to_payload(),
            crawl_session_id=crawl_session_id,
            canonical_property_id=canon_id,
            match_confidence=draft.confidence,
            match_explanation=explanation_dict(match_result),
            review_status=review_status,
        )
        db.add(raw)
        db.flush()

        if review_status == "auto_promoted" and canon_id is not None:
            db.add(ListingHistory(
                raw_listing_id=raw.id,
                canonical_property_id=canon_id,
                event_type="first_seen",
                price_observed=draft.price_parsed,
                availability="available",
                crawl_session_id=crawl_session_id,
            ))
        stats["new"] += 1

    db.commit()
    return stats


# --------------------------------------------------------------------------- #
# Admin review (universal-scraper promotion)
# --------------------------------------------------------------------------- #
def promote_raw_listing(db: Session, raw_listing_id: int,
                        action: str = "approve") -> dict:
    """Human review of a pending universal-scraper listing.

    approve: run match-key resolution; link to an existing canonical if a
        match is found, else create a new one. Set review_status to
        'human_approved', backdate a `first_seen` history event to the
        listing's crawled_at so the property's age is preserved.
    reject: set review_status to 'rejected' (the raw_listing stays for audit
        but is never promoted).
    Returns a small status dict.
    """
    from scrapers.drafts import RawListingDraft
    from scrapers.utils import detect_city, detect_neighborhood, normalize_text

    raw = db.query(RawListing).filter(RawListing.id == raw_listing_id).first()
    if raw is None:
        return {"ok": False, "error": "raw_listing not found"}
    if action == "reject":
        raw.review_status = "rejected"
        db.commit()
        return {"ok": True, "review_status": "rejected"}
    if action != "approve":
        return {"ok": False, "error": f"unknown action {action!r}"}
    if raw.review_status not in ("pending", "auto_promoted", "human_approved"):
        return {"ok": False, "error": f"cannot approve listing in status {raw.review_status!r}"}

    # Rebuild a minimal draft from the stored raw fields to feed the matcher.
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
    match_result = find_canonical_match(db, draft, location_id)
    if match_result.auto_promote and match_result.canonical_id:
        canon_id = match_result.canonical_id
    else:
        canon = create_canonical(db, draft, location_id)
        canon_id = canon.id

    raw.canonical_property_id = canon_id
    raw.review_status = "human_approved"
    raw.match_explanation = explanation_dict(match_result)

    # Backdate a first_seen event to when the page was actually crawled.
    db.add(ListingHistory(
        raw_listing_id=raw.id,
        canonical_property_id=canon_id,
        event_type="first_seen",
        price_observed=raw.price_parsed,
        availability="available",
        observed_at=raw.crawled_at,
        crawl_session_id=raw.crawl_session_id,
    ))
    db.commit()
    return {"ok": True, "review_status": "human_approved",
            "canonical_property_id": canon_id,
            "classification": match_result.classification}


# --------------------------------------------------------------------------- #
# Post-crawl cleanup
# --------------------------------------------------------------------------- #
def mark_removed(db: Session, source_id: int, current_crawl_session_id,
                 lookback_hours: int = 48) -> int:
    """Mark raw_listings of `source_id` whose latest crawl_session_id != the
    current one as removed (append an availability_change event). Returns the
    count of newly-removed listings. Only considers listings seen recently
    enough that a disappearance is meaningful (avoids re-flagging old ones)."""
    from datetime import timedelta
    threshold = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    rows = db.query(RawListing).filter(
        RawListing.source_id == source_id,
        RawListing.crawled_at >= threshold,
        RawListing.crawl_session_id != current_crawl_session_id,
    ).all()
    count = 0
    for raw in rows:
        latest = _latest_event(db, raw.id)
        if latest and latest.event_type == "removed":
            continue
        if raw.canonical_property_id:
            db.add(ListingHistory(
                raw_listing_id=raw.id,
                canonical_property_id=raw.canonical_property_id,
                event_type="removed",
                availability=None,
                crawl_session_id=current_crawl_session_id,
                diff={"old_availability": latest.availability if latest else "available",
                      "new_availability": "removed"},
            ))
            count += 1
    db.commit()
    return count


# --------------------------------------------------------------------------- #
# Best-price recompute
# --------------------------------------------------------------------------- #
def recompute_canonical_prices(db: Session) -> dict:
    """Recompute current_best_price for ALL canonical properties from their
    linked raw_listings. Sets to MIN(price_parsed) where valid prices exist,
    or None if no linked raw_listing has a positive price_parsed.

    This fixes stale and missing best prices that accumulate when listings are
    removed or when ingest's incremental update misses a case. Should be called
    after every crawl run (see main.py) and is also exposed via
    `python cli.py recompute-prices` for manual triggering.
    """
    stats = {"updated": 0, "cleared": 0, "unchanged": 0}
    canons = db.query(CanonicalProperty).all()
    for canon in canons:
        prices = [r.price_parsed for r in db.query(RawListing).filter(
            RawListing.canonical_property_id == canon.id,
            RawListing.price_parsed.isnot(None),
            RawListing.price_parsed > 0,
        ).all()]
        if not prices:
            if canon.current_best_price is not None:
                canon.current_best_price = None
                stats["cleared"] += 1
            else:
                stats["unchanged"] += 1
            continue
        best = min(prices)
        if canon.current_best_price != best:
            canon.current_best_price = best
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1
    db.commit()
    return stats


# --------------------------------------------------------------------------- #
# Backfill canonicals (location, match_key, structured fields)
# --------------------------------------------------------------------------- #
def backfill_canonicals(db: Session) -> dict:
    """Re-resolve location_id, match_key, and structured fields (bathrooms,
    area_sqm) for existing canonicals using the improved extractors and
    location resolver. Fixes canonicals created before the data-quality fixes.

    For each canonical, picks the most-recent linked raw_listing as the source
    of truth for location_raw and payload fields. Does NOT modify raw_listings
    (they are immutable) — only updates canonical_properties.
    """
    stats = {
        "locations_resolved": 0, "match_keys_updated": 0,
        "bathrooms_filled": 0, "area_filled": 0, "unchanged": 0,
    }
    canons = db.query(CanonicalProperty).all()
    for canon in canons:
        raw = db.query(RawListing).filter(
            RawListing.canonical_property_id == canon.id
        ).order_by(desc(RawListing.crawled_at)).first()
        if not raw:
            continue

        changed = False

        # Skip location resolution for canonicals that already have a
        # location_id — resolve_location() creates new Location rows as a
        # side effect, which produced orphaned fake neighborhoods (gas
        # stations, landmarks) when re-probing titles/descriptions.
        if canon.location_id is not None:
            # Use the existing location for match_key recomputation.
            loc = db.query(Location).filter(Location.id == canon.location_id).first()
            if loc:
                resolved_probe = f"{loc.neighborhood or ''} {loc.city}".strip()
            else:
                resolved_probe = None
        else:
            # Only resolve for canonicals with missing location_id.
            loc_id = None
            resolved_probe = None
            for probe in [raw.location_raw, raw.title_raw,
                          raw.description_raw[:200] if raw.description_raw else None]:
                if not probe:
                    continue
                loc_id = resolve_location(db, probe)
                if loc_id is not None:
                    resolved_probe = probe
                    break

            if loc_id is not None:
                canon.location_id = loc_id
                stats["locations_resolved"] += 1
                changed = True

        # 2. Recompute match_key with the (possibly newly) resolved location.
        if resolved_probe:
            city = detect_city(resolved_probe)
            neighborhood = detect_neighborhood(resolved_probe, city)
            if not city and neighborhood:
                city = infer_city_from_neighborhood(neighborhood)
            if city:
                new_mk = compute_match_key(canon.property_type, city, neighborhood)
                if new_mk and new_mk != canon.match_key:
                    canon.match_key = new_mk
                    stats["match_keys_updated"] += 1
                    changed = True

        # 3. Backfill bathrooms/area from the raw payload (the raw was
        #    extracted with the old code, but mapiole may have captured
        #    bathrooms that weren't propagated to the canonical).
        payload = raw.payload or {}
        if canon.bathrooms is None:
            baths = payload.get("bathrooms")
            if baths is not None and 0 < baths <= 50:
                canon.bathrooms = baths
                stats["bathrooms_filled"] += 1
                changed = True
        if canon.area_sqm is None:
            area = payload.get("area_sqm")
            if area is not None and area > 0:
                canon.area_sqm = area
                stats["area_filled"] += 1
                changed = True

        if not changed:
            stats["unchanged"] += 1

    db.commit()
    return stats