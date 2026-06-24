"""Pydantic response schemas for the CentralImmo API.

Aligned with the 4-layer data model (sources, raw_listings, canonical_properties,
listing_history, locations, neighborhood_analytics).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
class SourceSchema(BaseModel):
    id: int
    slug: str
    display_name: str
    site_url: str
    adapter_kind: str
    is_active: bool
    crawl_config: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Listings (the "Super-Annonce" view = canonical_property + best raw listing)
# --------------------------------------------------------------------------- #
class RawListingBrief(BaseModel):
    """One source's listing for a canonical property."""
    id: int
    source_slug: Optional[str] = None
    source_display_name: Optional[str] = None
    url_source: str
    price_parsed: Optional[int]
    currency: Optional[str]
    review_status: str
    match_confidence: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ListingHistoryEvent(BaseModel):
    id: int
    event_type: str
    price_observed: Optional[int]
    availability: Optional[str]
    observed_at: datetime
    diff: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class AnnonceBreve(BaseModel):
    """Lightweight listing for the home/search screens."""
    id: int
    title: str
    property_type: Optional[str]
    price: Optional[int]
    currency: str = "XAF"
    city: Optional[str]
    neighborhood: Optional[str]
    location_slug: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    area_sqm: Optional[float]
    images: List[str] = []
    best_source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnnonceDetaillee(AnnonceBreve):
    """Full detail — includes description, sources, price history, match info."""
    description: Optional[str]
    location_raw: Optional[str]
    sources: List[RawListingBrief] = []
    price_history: List[ListingHistoryEvent] = []
    match_explanation: Optional[dict] = None
    match_confidence: Optional[float] = None
    created_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class PriceAnalyse(BaseModel):
    """Market position of one property vs comparable listings
    (same property_type + same city). All prices in XAF.
    """
    listing_id: int
    price: Optional[int]
    city: Optional[str]
    property_type: Optional[str]
    sample_size: int
    min_price: Optional[int]
    max_price: Optional[int]
    mean_price: Optional[int]
    median_price: Optional[int]
    percentile: Optional[float]  # 0-100, where this price sits in the sample
    verdict: Optional[str]  # "below_market" | "around_market" | "above_market" | "insufficient_data"
    summary: str  # human-readable French summary for the UI callout


# --------------------------------------------------------------------------- #
# Locations & analytics
# --------------------------------------------------------------------------- #
class LocationSchema(BaseModel):
    id: int
    city: str
    neighborhood: Optional[str]
    slug: str
    lat: Optional[float]
    lng: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class NeighborhoodAnalyticsSchema(BaseModel):
    location_id: int
    city: str
    neighborhood: Optional[str]
    slug: str
    property_type: Optional[str]
    listing_count: int
    average_price: Optional[int]
    median_price: Optional[int]
    min_price: Optional[int]
    max_price: Optional[int]
    price_per_sqm: Optional[float]
    premium_score: Optional[float]
    demand_score: Optional[float]
    growth_score: Optional[float]
    activity_score: Optional[float]
    luxury_score: Optional[float]
    trend_direction: Optional[str]
    trend_pct: Optional[float]

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
class ReviewAction(BaseModel):
    action: str  # 'approve' | 'reject'


class SchedulerJobSchema(BaseModel):
    id: int
    job_type: str
    source_id: Optional[int]
    cron_expr: Optional[str]
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    status: str
    last_error: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class CrawlResult(BaseModel):
    ok: bool
    stats: Optional[dict] = None
    error: Optional[str] = None


class HealthSchema(BaseModel):
    status: str
    version: str
    database: str
    scheduler_running: bool


# --------------------------------------------------------------------------- #
# Security & intelligence profiles
# --------------------------------------------------------------------------- #
class CityProfileSchema(BaseModel):
    """City-level security and geopolitical intelligence."""
    id: int
    city: str
    region: Optional[str] = None
    security_rating: Optional[str] = None
    security_summary: Optional[str] = None
    current_threats: Optional[List[Any]] = None
    safest_zones: Optional[List[str]] = None
    emergency_contacts: Optional[List[Any]] = None
    travel_tips: Optional[str] = None
    curfew_info: Optional[str] = None
    population: Optional[int] = None
    area_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NeighborhoodProfileSchema(BaseModel):
    """Neighborhood-level security, amenities, and intelligence."""
    id: int
    location_id: Optional[int] = None
    city: str
    neighborhood: Optional[str] = None
    security_rating: Optional[str] = None
    security_notes: Optional[str] = None
    amenities: Optional[List[Any]] = None
    transport_info: Optional[str] = None
    real_estate_context: Optional[str] = None
    demographics: Optional[str] = None
    landmarks: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)