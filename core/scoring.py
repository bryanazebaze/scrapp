"""Neighborhood scoring functions (0-10 scale).

All scores are derived from platform data only — no external demographics.
Inputs are the raw aggregates computed by core.analytics (median price, days
on market, listing counts, trend slope, amenity counts). Each function
returns a float in [0, 10]; None is returned when the input is insufficient
to compute a meaningful score.
"""
from __future__ import annotations

from typing import Optional


def premium_score(neighborhood_median: float | None,
                  city_median: float | None) -> Optional[float]:
    """Percentile-rank style: how much pricier is this neighborhood vs its
    city. 0 = far below city median, 10 = 3x+ the city median.

    Uses a saturating formula so doubling the city median ~= 7 and tripling
    ~= 9, capping at 10 for >=3x.
    """
    if not neighborhood_median or not city_median or city_median <= 0:
        return None
    ratio = neighborhood_median / city_median
    # ratio 1.0 -> 5, ratio 2.0 -> ~7.5, ratio 3.0 -> ~9, capped at 10.
    score = min(10.0, 5.0 + (ratio - 1.0) * 2.5)
    return round(max(0.0, min(10.0, score)), 1)


def demand_score(median_days_on_market: float | None) -> Optional[float]:
    """Faster turnover = higher demand. Inverse of days-on-market, scaled so
    ~7 days (very hot) -> ~9, ~30 days -> ~6.5, ~90 days -> ~5, >180 -> ~3.

    None when no removed listings (no turnover data available).
    """
    if median_days_on_market is None:
        return None
    if median_days_on_market <= 0:
        return None
    import math
    if median_days_on_market < 1:
        median_days_on_market = 1.0
    # Gentle log curve: 7d->8.7, 30d->6.5, 90d->4.8, 180d->3.8.
    score = 10.0 - 3.5 * math.log10(median_days_on_market / 3.0)
    return round(max(1.0, min(10.0, score)), 1)


def growth_score(trend_pct: float | None) -> Optional[float]:
    """Map a 90-day price-trend percent to a 0-10 score. Flat = 5, +20% -> ~8,
    -20% -> ~2. Saturating so extreme moves flatten.
    """
    if trend_pct is None:
        return None
    # 5 + trend_pct/4, clamped to [0,10].
    score = 5.0 + (trend_pct / 4.0)
    return round(max(0.0, min(10.0, score)), 1)


def activity_score(listings_per_week: float | None,
                   reference_per_week: float | None = 5.0) -> Optional[float]:
    """Normalize listings-per-week to 0-10 against a reference (default 5/wk
    ~= a moderately active neighborhood). Saturating.
    """
    if listings_per_week is None or listings_per_week < 0:
        return None
    if reference_per_week <= 0:
        reference_per_week = 5.0
    # 1 listing/wk -> ~2, 5/wk -> ~5, 20/wk -> ~9 (saturating).
    import math
    score = 10.0 * (1 - math.exp(-listings_per_week / reference_per_week))
    return round(max(0.0, min(10.0, score)), 1)


def luxury_score(premium: float | None,
                 top_decile_share: float | None,
                 high_end_amenity_share: float | None) -> Optional[float]:
    """Weighted blend of premium score, share of listings in the city's top
    price decile, and share of listings mentioning high-end amenities
    (pool/garden/garage/terrace). All inputs are 0..1 fractions except premium
    which is 0..10. Returns 0..10.

    Weights: 0.50 * premium_norm + 0.30 * top_decile_share + 0.20 * amenity.
    """
    parts: list[float] = []
    weights: list[float] = []
    if premium is not None:
        parts.append((premium / 10.0) * 0.50)
        weights.append(0.50)
    if top_decile_share is not None:
        parts.append(max(0.0, min(1.0, top_decile_share)) * 0.30)
        weights.append(0.30)
    if high_end_amenity_share is not None:
        parts.append(max(0.0, min(1.0, high_end_amenity_share)) * 0.20)
        weights.append(0.20)
    if not parts:
        return None
    # Renormalize by available weights so a missing input doesn't deflate.
    total_weight = sum(weights)
    raw = sum(parts) / total_weight * 10.0 if total_weight else None
    return round(raw, 1) if raw is not None else None


def classify_premium(score: float | None) -> str:
    """Human label for a premium score."""
    if score is None:
        return "Unknown"
    if score >= 8.0:
        return "Premium"
    if score >= 6.0:
        return "Upscale"
    if score >= 4.0:
        return "Mid-tier"
    return "Affordable"


def classify_demand(score: float | None) -> str:
    if score is None:
        return "Unknown"
    if score >= 7.5:
        return "High Demand"
    if score >= 5.0:
        return "Moderate Demand"
    return "Low Demand"