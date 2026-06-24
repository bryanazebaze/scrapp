"""RawListingDraft — the canonical shape every scraper produces.

A `RawListingDraft` is the normalized intermediate representation between a
source-specific extractor (Mapiole, Kasastay, or the universal fallback) and
the ingest pipeline. It deliberately keeps BOTH the verbatim original fields
(`title_raw`, `price_raw`, `location_raw`, ...) and the parsed versions
(`price_parsed`, `images_raw`, ...) so the database can store originals
untouched while analytics work off the parsed values.

`payload` holds the full raw extraction trace (every field the source
returned), useful for audit and re-extraction without re-crawling.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class RawListingDraft:
    url_source: str
    title_raw: str
    price_raw: str | None = None
    price_parsed: int | None = None
    currency: str = "XAF"
    location_raw: str | None = None
    description_raw: str | None = None
    property_type_raw: str | None = None
    images_raw: list[str] = field(default_factory=list)
    # Structured fields that may or may not be available per source.
    bedrooms: int | None = None
    bathrooms: int | None = None
    area_sqm: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    amenities: list[str] = field(default_factory=list)
    # Confidence score from the scraper (0..1). Dedicated scrapers default to 1.0;
    # the universal scraper computes a heuristic score.
    confidence: float = 1.0
    # Full extraction trace for audit / re-extraction.
    payload: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict for storage in raw_listings.payload."""
        d = asdict(self)
        # payload is already nested; keep it as-is.
        return d