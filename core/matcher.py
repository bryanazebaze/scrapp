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
  - title_sim (rapidfuzz token_set_ratio) >= 80 AND DCS >= 0.75
    -> Confirmed Match (link)
  - best DCS >= 0.75 (with no hard-veto)        -> Probable Match (link)
  - otherwise                                    -> New Property

Hard vetoes (block auto-merge regardless of DCS):
  - Price difference > 25 % between the draft and the canonical
  - Bedrooms explicitly contradict (both present but different values)

The factors and classification are stored in raw_listings.match_explanation
so the admin review UI can show WHY two listings were (or were not) merged.

Classifications:
  Confirmed Match : DCS >= 0.85 (or title_sim >= 80 + DCS >= 0.75)
  Probable Match  : 0.75 <= DCS < 0.85
  New Property    : DCS < 0.75
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
    """Steep linear decay: 10 % gap → 0.70, 20 % → 0.40, 25 % → 0.25,
    33 % → ~0.01. This makes price a strong discriminator — the old
    formula (1 − ratio) scored a 33 % gap at 0.67, which was far too
    lenient and caused cross-source false merges."""
    if not p1 or not p2:
        return 0.3  # reduced from 0.5 — missing data should not inflate DCS
    lo, hi = min(p1, p2), max(p1, p2)
    if hi == 0:
        return 0.3
    ratio = abs(hi - lo) / float(hi)
    return max(1.0 - 3.0 * ratio, 0.0)


def _exact_or_neutral(a, b) -> float:
    if a is None or b is None:
        return 0.3  # reduced from 0.5
    return 1.0 if a == b else 0.0


def _surface_match(a: float | None, b: float | None, tol: float = 0.15) -> float:
    if a is None or b is None:
        return 0.3  # reduced from 0.5
    if a <= 0 or b <= 0:
        return 0.3
    lo, hi = min(a, b), max(a, b)
    return 1.0 if (hi - lo) / hi <= tol else 0.0


def _location_sim(loc_id_a: int | None, loc_id_b: int | None,
                  raw_a: str | None, raw_b: str | None) -> float:
    if loc_id_a and loc_id_b and loc_id_a == loc_id_b:
        return 1.0
    return _title_sim(raw_a, raw_b)


def _image_overlap(imgs_a: list[str], imgs_b: list[str]) -> float:
    # Cross-source image URLs almost never overlap (different sites host
    # different copies), so this factor is held neutral (0.3) when comparing
    # a draft to a canonical (which has no single image set). It still
    # contributes a small 0.05 weight; the other factors carry the signal.
    if not imgs_a or not imgs_b:
        return 0.3
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
    if dcs >= 0.75:
        return "Probable Match"
    return "New Property"


# --------------------------------------------------------------------------- #
# Matching against the canonical table
# --------------------------------------------------------------------------- #
TITLE_CONFIRM_THRESHOLD = 80  # rapidfuzz token_set_ratio, raised from 70
PROBABLE_DCS_THRESHOLD = 0.75  # raised from 0.65 — was causing false merges
PRICE_DIFF_MAX = 0.25  # hard veto: >25 % price gap blocks auto-merge


@dataclass
class MatchResult:
    canonical_id: int | None
    classification: str  # Confirmed Match | Probable Match | New Property
    dcs: float
    factors: MatchFactors
    auto_promote: bool  # True if the match is good enough to link automatically
    veto_reasons: list[str] = None  # populated when a hard veto blocked auto-merge


def find_canonical_match(db: Session, draft: RawListingDraft,
                         location_id: int | None) -> MatchResult:
    """Resolve a draft to a canonical property.

    1. Compute the coarse match_key (type + city + neighborhood). If no city
       can be parsed, skip key-matching — return New Property.
    2. Retrieve ALL canonicals sharing that key (a small candidate set).
    3. Compute DCS against each; track the best.
    4. Hard vetoes: price gap > 25 % or explicit bedroom contradiction block
       auto-merge regardless of DCS.
    5. If title_sim >= 80 AND DCS >= 0.75 and not vetoed -> Confirmed Match.
       Elif DCS >= 0.75 and not vetoed -> Probable Match (link).
       Else                             -> New Property.
    """
    city = detect_city(draft.location_raw)
    neighborhood = detect_neighborhood(draft.location_raw, city)
    mk = compute_match_key(draft.property_type_raw, city, neighborhood)
    if mk is None:
        return MatchResult(None, "New Property", 0.0,
                           MatchFactors(0, 0, 0, 0, 0, 0, 0), False, None)

    candidates = db.query(CanonicalProperty).filter(
        CanonicalProperty.match_key == mk
    ).all()
    if not candidates:
        return MatchResult(None, "New Property", 0.0,
                           MatchFactors(0, 0, 0, 0, 0, 0, 0), False, None)

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

    # --- Hard vetoes: block auto-merge regardless of DCS score ---
    vetoed = False
    veto_reasons = []

    # 1. Price-difference guard: > 25 % gap is almost certainly a different
    #    property or a different rental condition (e.g. 6-month vs 12-month
    #    lease). The old algorithm merged a 100 k / 150 k pair (50 % gap)
    #    because other factors compensated — that was a false positive.
    if draft.price_parsed and canon.current_best_price:
        price_diff = abs(draft.price_parsed - canon.current_best_price)
        price_hi = max(draft.price_parsed, canon.current_best_price)
        if price_diff / float(price_hi) > PRICE_DIFF_MAX:
            vetoed = True
            veto_reasons.append(
                f"price_diff_{price_diff / price_hi:.0%}"
            )

    # 2. Bedrooms hard veto: if both sides have explicit bedroom counts and
    #    they differ, this is very likely a different property. A studio (1
    #    bed) vs a 3-bedroom apartment should never auto-merge.
    if factors.bedrooms_match == 0.0:
        vetoed = True
        veto_reasons.append("bedrooms_contradict")

    # --- Title short-circuit: require BOTH high title similarity AND DCS ---
    if title_ratio >= TITLE_CONFIRM_THRESHOLD and dcs >= PROBABLE_DCS_THRESHOLD and not vetoed:
        return MatchResult(canon.id, "Confirmed Match", dcs, factors, True, None)
    classification = classify(dcs)
    auto = dcs >= PROBABLE_DCS_THRESHOLD and not vetoed
    return MatchResult(
        canon.id if auto else None, classification, dcs, factors, auto,
        veto_reasons if vetoed else None,
    )


def explanation_dict(result: MatchResult) -> dict:
    """Build the JSONB explanation stored on raw_listings.match_explanation."""
    out = {
        "classification": result.classification,
        "dcs": round(result.dcs, 4),
        "matched_canonical_id": result.canonical_id,
        "factors": {k: round(v, 4) for k, v in asdict(result.factors).items()},
        "auto_promoted": result.auto_promote,
    }
    if result.veto_reasons:
        out["veto_reasons"] = result.veto_reasons
    return out