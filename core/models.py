"""SQLAlchemy ORM models for the multi-layer data model.

Six core tables plus two operational tables (scheduler_jobs, neighborhood_analytics):

  sources              website metadata (one row per aggregated site)
  locations             normalized city/neighborhood (shared reference)
  raw_listings         immutable original scraped data (NEVER updated after insert)
  canonical_properties a real-world property (many raw listings -> one canonical)
  listing_history      append-only event log (price/availability changes)
  image_cache          optional downloaded-image cache (original URLs live in raw_listings)

  scheduler_jobs       scheduler run state (Phase 6)
  neighborhood_analytics  computed city/neighborhood scores cache (Phase 5)

Design rules enforced here:
- raw_listings is insert-only (idempotent on url_hash). Re-crawls become
  listing_history events, never row updates.
- canonical_properties is matched by `match_key` (deterministic hash of
  type+city+neighborhood+price_bucket+title_normalized) so dedup is an O(1)
  index lookup instead of a price-range scan.
- listing_history is append-only; price/availability changes are never
  overwritten (fixes the previous meilleur_prix overwrite bug).
- locations is a normalized reference; raw_listings keeps the verbatim
  location_raw string, canonical_properties points to a resolved location_id.
"""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, BigInteger, SmallInteger, String, Text, Boolean,
    Float, DateTime, ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


# --------------------------------------------------------------------------- #
# Reference data
# --------------------------------------------------------------------------- #
class Source(Base):
    """Metadata about an aggregated website (dedicated or universal scraper)."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(60), nullable=False, unique=True, index=True)
    display_name = Column(String(120), nullable=False)
    site_url = Column(String(500), nullable=False)
    # 'dedicated' = hand-written adapter (Mapiole, Kasastay)
    # 'universal' = heuristic fallback scraper
    adapter_kind = Column(String(30), nullable=False, default="dedicated")
    robots_txt_url = Column(String(500), nullable=True)
    # free-form per-source config: {headers, delay_range, pagination, cron, proxy_url}
    crawl_config = Column(JSONB, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    raw_listings = relationship("RawListing", back_populates="source")


class Location(Base):
    """Normalized city/neighborhood reference used for analytics grouping."""
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("city", "neighborhood", name="uq_location_city_neighborhood"),
        Index("idx_location_slug", "slug"),
        Index("idx_location_city", "city"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    city = Column(String(80), nullable=False)
    neighborhood = Column(String(120), nullable=True)
    district = Column(String(80), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    slug = Column(String(140), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    canonical_properties = relationship("CanonicalProperty", back_populates="location")


# --------------------------------------------------------------------------- #
# Listings & properties
# --------------------------------------------------------------------------- #
class RawListing(Base):
    """Immutable original scraped data. One row per unique source URL.

    Insert is idempotent on url_hash (sha256 of url_source). Re-crawling the
    same URL never creates a new row; instead the ingest pipeline compares
    the fresh scrape to the latest listing_history event for this row and
    appends a price_change / availability_change event if something moved.
    """
    __tablename__ = "raw_listings"
    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_raw_url_hash"),
        Index("idx_raw_source_crawled", "source_id", "crawled_at"),
        Index("idx_raw_canonical", "canonical_property_id"),
        Index("idx_raw_review", "review_status"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    url_source = Column(Text, nullable=False)
    url_hash = Column(String(64), nullable=False)

    # Verbatim original fields — NEVER transformed
    title_raw = Column(Text, nullable=False)
    price_raw = Column(Text, nullable=True)
    price_parsed = Column(BigInteger, nullable=True)
    currency = Column(String(10), nullable=True, default="XAF")
    location_raw = Column(Text, nullable=True)
    description_raw = Column(Text, nullable=True)
    property_type_raw = Column(String(60), nullable=True)
    # Original image URLs (canonical record); downloads are a cache, see ImageCache
    images_raw = Column(JSONB, nullable=True)
    # Full scraper output dict, untouched, for audit/re-extraction
    payload = Column(JSONB, nullable=True)

    crawl_session_id = Column(UUID(as_uuid=True), nullable=False)
    crawled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Link to the real-world property (nullable until matched/approved)
    canonical_property_id = Column(BigInteger, ForeignKey("canonical_properties.id"),
                                   nullable=True, index=True)
    match_confidence = Column(Float, nullable=True)
    match_explanation = Column(JSONB, nullable=True)
    # pending | auto_promoted | human_approved | rejected
    review_status = Column(String(20), nullable=False, default="pending", index=True)

    canonical_property = relationship("CanonicalProperty", back_populates="raw_listings")
    source = relationship("Source", back_populates="raw_listings")
    history = relationship("ListingHistory", back_populates="raw_listing",
                           cascade="all, delete-orphan")
    translations = relationship("ListingTranslation", back_populates="raw_listing",
                                cascade="all, delete-orphan")


class ListingTranslation(Base):
    """Translated description for a raw listing.

    raw_listings is immutable (project convention), so translations live in
    a side table keyed by (raw_listing_id, language). Generated by the
    back-translation scripts; served based on the request's Accept-Language.
    """
    __tablename__ = "listing_translations"
    __table_args__ = (
        UniqueConstraint("raw_listing_id", "language",
                         name="uq_listing_translation_lang"),
        Index("idx_listing_translations_listing", "raw_listing_id"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    raw_listing_id = Column(BigInteger, ForeignKey("raw_listings.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    language = Column(String(5), nullable=False)  # 'en' | 'fr'
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    raw_listing = relationship("RawListing", back_populates="translations")


class CanonicalProperty(Base):
    """A real-world property. Many raw listings (from different sites) can
    point to one canonical property. Identified by a synthetic id plus a
    deterministic `match_key` for dedup.
    """
    __tablename__ = "canonical_properties"
    __table_args__ = (
        # match_key is a coarse candidate-retrieval bucket (type+city+
        # neighborhood), NOT a unique identifier — multiple distinct
        # properties in the same bucket share a key and the DCS disambiguates.
        Index("idx_canonical_match_key", "match_key"),
        Index("idx_canonical_location", "location_id"),
        Index("idx_canonical_type_loc", "property_type", "location_id"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    # sha1(property_type_normalized | city_slug | neighborhood_slug) — a coarse
    # candidate-retrieval bucket (see core/matcher.py:compute_match_key). NOT
    # unique: multiple distinct properties in the same type+city+neighborhood
    # share a key; the DCS disambiguates. If no city can be parsed, a per-row
    # 'noloc:' hash is used so the property is still stored.
    match_key = Column(String(64), nullable=False)
    title_canonical = Column(Text, nullable=False)
    title_normalized = Column(Text, nullable=False)
    property_type = Column(String(30), nullable=False, index=True)
    location_id = Column(BigInteger, ForeignKey("locations.id"), nullable=True)

    bedrooms = Column(SmallInteger, nullable=True)
    bathrooms = Column(SmallInteger, nullable=True)
    area_sqm = Column(Float, nullable=True)

    # Best (lowest) price currently observed across sources; recomputed from
    # raw_listings, never the source of truth for history.
    current_best_price = Column(BigInteger, nullable=True)
    current_availability = Column(String(20), nullable=True, default="available")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    location = relationship("Location", back_populates="canonical_properties")
    raw_listings = relationship("RawListing", back_populates="canonical_property")
    history = relationship("ListingHistory", back_populates="canonical_property")


class ListingHistory(Base):
    """Append-only event log. One row per observed change.

    Event types: first_seen | price_change | availability_change | appeared |
    removed. The ingest pipeline compares a fresh scrape to the latest event
    for a raw_listing_id and only appends when price/availability changed.
    """
    __tablename__ = "listing_history"
    __table_args__ = (
        Index("idx_history_canon_time", "canonical_property_id", "observed_at"),
        Index("idx_history_raw", "raw_listing_id"),
        Index("idx_history_raw_latest", "raw_listing_id", "observed_at"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    raw_listing_id = Column(BigInteger, ForeignKey("raw_listings.id"), nullable=False)
    canonical_property_id = Column(BigInteger, ForeignKey("canonical_properties.id"), nullable=False)
    event_type = Column(String(30), nullable=False)
    price_observed = Column(BigInteger, nullable=True)
    availability = Column(String(20), nullable=True)
    observed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    crawl_session_id = Column(UUID(as_uuid=True), nullable=False)
    # {old: ..., new: ...} for change events; null for first_seen/removed
    diff = Column(JSONB, nullable=True)

    raw_listing = relationship("RawListing", back_populates="history")
    canonical_property = relationship("CanonicalProperty", back_populates="history")


# --------------------------------------------------------------------------- #
# Operational tables
# --------------------------------------------------------------------------- #
class ImageCache(Base):
    """UNUSED — retained for schema compatibility. Images are now served
    directly from their original URLs (raw_listings.images_raw); no local
    caching is performed. The table still exists in the migration for
    backward compatibility but is never populated. Safe to drop in a future
    migration once confirmed unnecessary.
    """
    __tablename__ = "image_cache"
    __table_args__ = (
        Index("idx_image_cache_source", "source_id"),
    )

    url_hash = Column(String(64), primary_key=True)
    original_url = Column(Text, nullable=False)
    local_path = Column(Text, nullable=False)
    bytes = Column(Integer, nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SchedulerJob(Base):
    """State of scheduled jobs (crawl / refresh / analytics recompute)."""
    __tablename__ = "scheduler_jobs"
    __table_args__ = (
        Index("idx_scheduler_jobs_source", "source_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(40), nullable=False)  # crawl_all|crawl_source|refresh|analytics
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    cron_expr = Column(String(60), nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="scheduled")  # scheduled|running|succeeded|failed
    last_error = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                         onupdate=func.now(), nullable=False)


class NeighborhoodAnalytics(Base):
    """Cached city/neighborhood market-intelligence scores.

    Recomputed weekly by the scheduler; `GET /neighborhoods/{slug}` reads from
    here plus a live delta. Storing avoids recompute on every request.
    """
    __tablename__ = "neighborhood_analytics"
    __table_args__ = (
        UniqueConstraint("location_id", "property_type", "period", name="uq_analytics_loc_type_period"),
        Index("idx_analytics_location", "location_id"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    location_id = Column(BigInteger, ForeignKey("locations.id"), nullable=False)
    property_type = Column(String(30), nullable=True)  # null = all types
    # 'current' snapshot or 'YYYY-MM' rolling window
    period = Column(String(20), nullable=False, default="current")

    listing_count = Column(Integer, nullable=False, default=0)
    average_price = Column(BigInteger, nullable=True)
    median_price = Column(BigInteger, nullable=True)
    min_price = Column(BigInteger, nullable=True)
    max_price = Column(BigInteger, nullable=True)
    price_per_sqm = Column(Float, nullable=True)

    # Scores 0..10
    premium_score = Column(Float, nullable=True)
    demand_score = Column(Float, nullable=True)
    growth_score = Column(Float, nullable=True)
    activity_score = Column(Float, nullable=True)
    luxury_score = Column(Float, nullable=True)

    trend_direction = Column(String(10), nullable=True)  # up|down|flat
    trend_pct = Column(Float, nullable=True)

    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# --------------------------------------------------------------------------- #
# Security & geopolitical intelligence profiles
# --------------------------------------------------------------------------- #
class CityProfile(Base):
    """City-level security and geopolitical intelligence.

    One row per city. Provides a high-level security overview (risk rating,
    threat landscape, safest zones, emergency contacts, curfew info) to
    contextualize listings and inform prospective tenants/buyers.
    """
    __tablename__ = "city_profiles"
    __table_args__ = (
        Index("idx_city_profiles_city", "city"),
    )

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(80), nullable=False, unique=True, index=True)
    region = Column(String(80), nullable=True)  # e.g. "Littoral", "Centre"
    security_rating = Column(String(20), nullable=True)  # Low Risk|Moderate Risk|High Risk
    security_summary = Column(Text, nullable=True)  # 2-3 paragraph overview
    # array of {type, description, severity} objects
    current_threats = Column(JSONB, nullable=True)
    # array of neighborhood name strings
    safest_zones = Column(JSONB, nullable=True)
    # array of {service, number, notes} objects
    emergency_contacts = Column(JSONB, nullable=True)
    travel_tips = Column(Text, nullable=True)
    curfew_info = Column(Text, nullable=True)
    population = Column(Integer, nullable=True)
    area_description = Column(Text, nullable=True)  # general description of the city
    # English mirrors (served when Accept-Language: en); NULL until back-translated
    security_summary_en = Column(Text, nullable=True)
    travel_tips_en = Column(Text, nullable=True)
    curfew_info_en = Column(Text, nullable=True)
    area_description_en = Column(Text, nullable=True)
    current_threats_en = Column(JSONB, nullable=True)
    safest_zones_en = Column(JSONB, nullable=True)
    emergency_contacts_en = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)


class NeighborhoodProfile(Base):
    """Neighborhood-level security and intelligence profile.

    Optionally links to a locations row for analytics joining. Unique per
    (city, neighborhood) so each neighborhood has at most one profile per city.
    """
    __tablename__ = "neighborhood_profiles"
    __table_args__ = (
        UniqueConstraint("city", "neighborhood", name="uq_neighborhood_profile_city_neighborhood"),
        Index("idx_neighborhood_profiles_city", "city"),
        Index("idx_neighborhood_profiles_location", "location_id"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    location_id = Column(BigInteger, ForeignKey("locations.id"), nullable=True, index=True)
    city = Column(String(80), nullable=False, index=True)
    neighborhood = Column(String(120), nullable=True)
    security_rating = Column(String(20), nullable=True)
    security_notes = Column(Text, nullable=True)
    # array of {type, name, description} objects
    amenities = Column(JSONB, nullable=True)
    transport_info = Column(Text, nullable=True)
    real_estate_context = Column(Text, nullable=True)  # market trends, typical price ranges
    demographics = Column(Text, nullable=True)
    # array of strings (landmark names)
    landmarks = Column(JSONB, nullable=True)
    # array of strings like "flooding", "traffic", "crime"
    risk_factors = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)  # rich description of the neighborhood
    # English mirrors (served when Accept-Language: en); NULL until back-translated
    security_notes_en = Column(Text, nullable=True)
    transport_info_en = Column(Text, nullable=True)
    real_estate_context_en = Column(Text, nullable=True)
    demographics_en = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    amenities_en = Column(JSONB, nullable=True)
    landmarks_en = Column(JSONB, nullable=True)
    risk_factors_en = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    location = relationship("Location")