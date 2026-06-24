"""Duplicate detection and property matching.

Replaces the legacy `trouver_doublon` (core/fusion.py:45-66), which scanned the
whole annonces table for price within +/-15% and then rapidfuzz >= 70 on the
title. That scan returns few candidates in practice but runs per-row.

New approach (ADR-004): a coarse `match_key` retrieves candidates by index,
then a composite Duplicate Confidence Score (DCS) disambiguates among them.

match_key = sha1(property_type | city_slug | neighborhood_slug)
  - It is a CANDIDATE-RETRIEVAL bucket, NOT a unique identifier. Multiple
    distinct properties in the same type+city+neighborhood share a key; title
    similarity + DCS tell them apart. (An earlier version put the title and a
    price bucket in the key — that was too strict: the same property
    advertised on two sites with slightly different titles got two keys and
    was never merged.)
  - Indexed, non-unique (see migration 0002 which drops the original unique
    constraint added in 0001).
  - If no city can be parsed from the location, key-based matching is skipped
    (the draft becomes a New Property / goes to review) — merging on type
    alone is too loose.

For a new draft we query every canonical with the same match_key, compute
DCS against each, and pick the best:
  - title_sim (rapidfuzz token_set_ratio) >= 80  -> Confirmed Match (link)
  - best DCS >= 0.65                              -> Probable Match (link)
  - otherwise                                     -> New Property

The factors and classification are stored in raw_listings.match_explanation
so the admin review UI can show WHY two listings were (or were not) merged.

Classifications:
  Confirmed Match : DCS >= 0.85 (or title_sim >= 80)
  Probable Match  : 0.65 <= DCS < 0.85
  New Property    : DCS < 0.65
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from core.models import CanonicalProperty, Location
from scrapers.drafts import RawListingDraft
from scrapers.utils import normalize_text, slugify, detect_city, detect_neighborhood


def compute_match_key(property_type: str | None, city: str | None,
                      neighborhood: str | None) -> str | None:
    """Coarse candidate-retrieval key. Returns None when no city can be
    parsed (signalling 'do not key-match'). MUST stay in sync with the
    recompute logic in alembic/versions/0002_drop_match_key_unique.py."""
    if not city:
        return None
    parts = [
        normalize_text(property_type) or "unknown",
        slugify(city) or "unknown",
        slugify(neighborhood) or "unknown",
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Composite Duplicate Confidence Score
# --------------------------------------------------------------------------- #
@dataclass
class MatchFactors:
    title_sim: float
    price_proximity: float
    type_match: float
    surface_match: float
    bedrooms_match: float
    location_sim: float
    image_overlap: float


def _title_sim(a: str | None, b: str | None) -> float:
    na, nb = normalize_text(a), normalize_text(b)
    if not na or not nb:
        return 0.0
    return fuzz.token_set_ratio(na, nb) / 100.0


def _price_proximity(p1: int | None, p2: int | None) -> float:
    if not p1 or not p2:
        return 0.5  # neutral when a side is missing
    lo, hi = min(p1, p2), max(p1, p2)
    if hi == 0:
        return 0.5
    return 1.0 - min(abs(hi - lo) / float(hi), 1.0)


def _exact_or_neutral(a, b) -> float:
    if a is None or b is None:
        return 0.5
    return 1.0 if a == b else 0.0


def _surface_match(a: float | None, b: float | None, tol: float = 0.15) -> float:
    if a is None or b is None:
        return 0.5
    if a <= 0 or b <= 0:
        return 0.5
    lo, hi = min(a, b), max(a, b)
    return 1.0 if (hi - lo) / hi <= tol else 0.0


def _location_sim(loc_id_a: int | None, loc_id_b: int | None,
                  raw_a: str | None, raw_b: str | None) -> float:
    if loc_id_a and loc_id_b and loc_id_a == loc_id_b:
        return 1.0
    return _title_sim(raw_a, raw_b)


def _image_overlap(imgs_a: list[str], imgs_b: list[str]) -> float:
    # Cross-source image URLs almost never overlap (different sites host
    # different copies), so this factor is held neutral (0.5) when comparing
    # a draft to a canonical (which has no single image set). It still
    # contributes a small 0.05 weight; the other factors carry the signal.
    if not imgs_a or not imgs_b:
        return 0.5
    ha = {hashlib.md5(u.encode("utf-8")).hexdigest() for u in imgs_a if u}
    hb = {hashlib.md5(u.encode("utf-8")).hexdigest() for u in imgs_b if u}
    if not ha or not hb:
        return 0.5
    inter = len(ha & hb)
    return inter / max(len(ha | hb), 1)


def compute_dcs(draft: RawListingDraft, canonical: CanonicalProperty,
                draft_location_id: int | None = None) -> tuple[float, MatchFactors]:
    """Composite DCS between a new draft and an existing canonical property."""
    f = MatchFactors(
        title_sim=_title_sim(draft.title_raw, canonical.title_canonical),
        price_proximity=_price_proximity(draft.price_parsed, canonical.current_best_price),
        type_match=1.0 if (draft.property_type_raw or "").lower() == (canonical.property_type or "").lower() else 0.0,
        surface_match=_surface_match(draft.area_sqm, canonical.area_sqm),
        bedrooms_match=_exact_or_neutral(draft.bedrooms, canonical.bedrooms),
        location_sim=_location_sim(draft_location_id, canonical.location_id,
                                    draft.location_raw, None),
        image_overlap=_image_overlap(draft.images_raw or [], []),
    )
    dcs = (
        0.30 * f.title_sim
        + 0.20 * f.price_proximity
        + 0.15 * f.type_match
        + 0.15 * f.surface_match
        + 0.10 * f.bedrooms_match
        + 0.05 * f.location_sim
        + 0.05 * f.image_overlap
    )
    return dcs, f


def classify(dcs: float) -> str:
    if dcs >= 0.85:
        return "Confirmed Match"
    if dcs >= 0.65:
        return "Probable Match"
    return "New Property"


# --------------------------------------------------------------------------- #
# Matching against the canonical table
# --------------------------------------------------------------------------- #
TITLE_CONFIRM_THRESHOLD = 80  # rapidfuzz token_set_ratio, raised from 70
PROBABLE_DCS_THRESHOLD = 0.65


@dataclass
class MatchResult:
    canonical_id: int | None
    classification: str  # Confirmed Match | Probable Match | New Property
    dcs: float
    factors: MatchFactors
    auto_promote: bool  # True if the match is good enough to link automatically


def find_canonical_match(db: Session, draft: RawListingDraft,
                         location_id: int | None) -> MatchResult:
    """Resolve a draft to a canonical property.

    1. Compute the coarse match_key (type + city + neighborhood). If no city
       can be parsed, skip key-matching — return New Property.
    2. Retrieve ALL canonicals sharing that key (a small candidate set).
    3. Compute DCS against each; track the best.
    4. If best title_sim >= 80 -> Confirmed Match (link).
       Elif best DCS >= 0.65  -> Probable Match (link with explanation).
       Else                  -> New Property.
    """
    city = detect_city(draft.location_raw)
    neighborhood = detect_neighborhood(draft.location_raw, city)
    mk = compute_match_key(draft.property_type_raw, city, neighborhood)
    if mk is None:
        return MatchResult(None, "New Property", 0.0,
                           MatchFactors(0, 0, 0, 0, 0, 0, 0), False)

    candidates = db.query(CanonicalProperty).filter(
        CanonicalProperty.match_key == mk
    ).all()
    if not candidates:
        return MatchResult(None, "New Property", 0.0,
                           MatchFactors(0, 0, 0, 0, 0, 0, 0), False)

    best: tuple[float, MatchFactors, CanonicalProperty] | None = None
    for canon in candidates:
        dcs, factors = compute_dcs(draft, canon, draft_location_id=location_id)
        if best is None or dcs > best[0]:
            best = (dcs, factors, canon)

    dcs, factors, canon = best
    title_ratio = fuzz.token_set_ratio(
        normalize_text(draft.title_raw),
        normalize_text(canon.title_canonical),
    )
    if title_ratio >= TITLE_CONFIRM_THRESHOLD:
        return MatchResult(canon.id, "Confirmed Match", dcs, factors, True)
    classification = classify(dcs)
    auto = dcs >= PROBABLE_DCS_THRESHOLD
    return MatchResult(canon.id if auto else None, classification, dcs, factors, auto)


def explanation_dict(result: MatchResult) -> dict:
    """Build the JSONB explanation stored on raw_listings.match_explanation."""
    return {
        "classification": result.classification,
        "dcs": round(result.dcs, 4),
        "matched_canonical_id": result.canonical_id,
        "factors": {k: round(v, 4) for k, v in asdict(result.factors).items()},
        "auto_promoted": result.auto_promote,
    }