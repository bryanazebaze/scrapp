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
    """Lightweight listing for the home/search/screens."""
    id: int
    title: str
    property_type: Optional[str]
    price: Optional[int]
    currency: str = "XAF"
    city: Optional[str]
    neighborhood: Optional[str]
    location_slug: Optional[str]
    lat: Optional[float] = None
    lng: Optional[float] = None
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

    Category-aware:
      - Structure (Appartement/Maison/...): comparison_metric="total_price";
        min_price/max_price/mean_price populated; price-per-sqm fields NULL.
      - Land (Terrain): comparison_metric="price_per_sqm";
        min_price_per_sqm/max_price_per_sqm/avg_price_per_sqm populated;
        total-price fields NULL.
      `savings` is positive when the listing is below market.
      `fallback_level` is "neighborhood" when comparables came from the same
      neighborhood, "city" when the neighborhood had < 3 comparables and the
      set was widened to the whole city.
    """
    listing_id: int
    price: Optional[int]
    city: Optional[str]
    property_type: Optional[str]
    category: Optional[str] = None  # "Structure" | "Land" | None
    comparison_metric: Optional[str] = None  # "total_price" | "price_per_sqm"
    sample_size: int
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    mean_price: Optional[int] = None
    median_price: Optional[int] = None
    min_price_per_sqm: Optional[float] = None
    max_price_per_sqm: Optional[float] = None
    avg_price_per_sqm: Optional[float] = None
    avg_comparison: Optional[float] = None  # mean of comparables' metric
    listing_comparison: Optional[float] = None  # listing's value for the metric
    savings: Optional[float] = None  # positive = below market
    fallback_level: Optional[str] = None  # "neighborhood" | "city" | None
    percentile: Optional[float] = None  # 0-100, where this price sits in the sample
    verdict: Optional[str] = None  # "below_market" | "around_market" | "above_market" | "insufficient_data"
    summary: str = ""  # human-readable French summary for the UI callout


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
    location_id: Optional[int] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    slug: Optional[str] = None
    property_type: Optional[str] = None
    category: Optional[str] = None  # "Structure" | "Land" | None
    listing_count: int = 0
    average_price: Optional[int] = None
    median_price: Optional[int] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    price_per_sqm: Optional[float] = None
    min_price_per_sqm: Optional[float] = None
    max_price_per_sqm: Optional[float] = None
    avg_price_per_sqm: Optional[float] = None
    fallback_level: Optional[str] = None  # "neighborhood" | "city" | None
    premium_score: Optional[float] = None
    demand_score: Optional[float] = None
    growth_score: Optional[float] = None
    activity_score: Optional[float] = None
    luxury_score: Optional[float] = None
    trend_direction: Optional[str] = None
    trend_pct: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
class ReviewAction(BaseModel):
    action: str  # 'approve' | 'reject' | 'confirm_duplicate' | 'not_duplicate'


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


class JobUpdateSchema(BaseModel):
    """PATCH /admin/jobs/{job_id} body — either field is optional."""
    cron_expr: Optional[str] = None
    paused: Optional[bool] = None


class JobSchemaOut(BaseModel):
    """Enhanced job view: SchedulerJob row + live APScheduler next_run_time + paused flag."""
    id: int
    job_type: str
    source_id: Optional[int] = None
    cron_expr: Optional[str] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: str
    last_error: Optional[str] = None
    paused: bool = False
    job_aps_id: Optional[str] = None

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


# --------------------------------------------------------------------------- #
# AI Chat
# --------------------------------------------------------------------------- #
class ChatMessage(BaseModel):
    """One message in the chat conversation history."""
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request body for POST /chat."""
    message: str
    history: List[ChatMessage] = []
    language: str = "fr"  # "fr" or "en" — controls AI response language


class ChatResponse(BaseModel):
    """Response from the AI chat agent."""
    reply: str
    properties: List[AnnonceBreve] = []
    tool_used: Optional[str] = None
    tool_metadata: Optional[dict] = None


# --------------------------------------------------------------------------- #
# Payments
# --------------------------------------------------------------------------- #
class UpgradeRequest(BaseModel):
    """Request body for POST /payments/upgrade."""
    phone: str
    channel: str  # "cm.mtn" | "cm.orange"
    amount: int = 2000  # XAF


class PaymentStatusResponse(BaseModel):
    """Response for GET /payments/{reference}/status."""
    status: str
    is_paid: bool
    reference: str


class PaymentMeResponse(BaseModel):
    """Response for GET /payments/me."""
    is_paid: bool
    paid_at: Optional[str] = None
    amount: Optional[int] = None


# --------------------------------------------------------------------------- #
# End-user auth (email/password)
# --------------------------------------------------------------------------- #
class UserRegisterSchema(BaseModel):
    """POST /auth/register body."""
    display_name: str
    email: str
    phone: Optional[str] = None
    password: str


class UserLoginSchema(BaseModel):
    """POST /auth/login body."""
    email: str
    password: str


class UserOutSchema(BaseModel):
    """User record returned to clients (no password_hash)."""
    id: int
    email: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserTokenSchema(BaseModel):
    """POST /auth/register|login response."""
    access_token: str
    token_type: str = "bearer"
    user: UserOutSchema


# --------------------------------------------------------------------------- #
# Admin auth
# --------------------------------------------------------------------------- #
class AdminLoginSchema(BaseModel):
    """POST /admin/login body — identifier may be username or email."""
    identifier: str
    password: str


class AdminUserOutSchema(BaseModel):
    """Admin user returned to clients (no password_hash)."""
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True
    is_superadmin: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminTokenSchema(BaseModel):
    """POST /admin/login response."""
    access_token: str
    token_type: str = "bearer"
    admin: AdminUserOutSchema