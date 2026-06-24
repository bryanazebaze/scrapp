"""SourceAdapter — the common interface every scraper implements.

Both dedicated adapters (Mapiole, Kasastay) and the universal fallback adapter
implement this interface, so the ingest pipeline and scheduler treat them
identically. The previous `BaseScraper.scrape() -> List[Annonce]` returned ORM
models directly, coupling scraping to persistence; adapters now return
`RawListingDraft` (a plain dataclass) and the ingest pipeline owns persistence.

A `RawListingDraft` keeps the verbatim original fields (title_raw, price_raw,
location_raw, images_raw) alongside parsed values so raw_listings can store
originals untouched while analytics use the parsed ones.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .drafts import RawListingDraft


class SourceAdapter(ABC):
    """Common interface for all property-source scrapers.

    Subclasses set `platform_slug`, `base_url` and (optionally) `source_id`
    (looked up from the `sources` table at runtime by the orchestrator).
    """

    platform_slug: str = "base"
    base_url: str = ""
    adapter_kind: str = "dedicated"  # 'dedicated' | 'universal'

    def __init__(self, source_id: Optional[int] = None) -> None:
        self.source_id = source_id

    @abstractmethod
    def fetch_listings(self, max_pages: int | None = None) -> list[RawListingDraft]:
        """Discover listing URLs from the source's catalog/index pages and
        return one RawListingDraft per listing (with detail fields filled).
        For dedicated adapters this parses the catalog and visits each detail
        page; for the universal adapter it runs URL discovery + card detection
        + extraction. `max_pages` caps pagination (None = site default)."""
        ...

    @abstractmethod
    def fetch_details(self, listing_url: str) -> Optional[RawListingDraft]:
        """Fetch one listing's detail page and extract fields. Returns None
        on failure (network error, page not found, no extractable title)."""
        ...

    @abstractmethod
    def normalize_data(self, raw: dict) -> RawListingDraft:
        """Map a source-specific dict of extracted fields to the canonical
        RawListingDraft schema. Must NOT transform the raw strings — keep
        title_raw/price_raw/location_raw verbatim alongside parsed values."""
        ...

    def validate_data(self, draft: RawListingDraft) -> tuple[bool, list[str]]:
        """Default validity check: a listing needs a title AND (a price OR a
        location) AND at least one image URL. Adapters may override for
        stricter checks. Returns (is_valid, reasons)."""
        reasons: list[str] = []
        if not draft.title_raw or not draft.title_raw.strip():
            reasons.append("missing title")
        has_price = draft.price_parsed is not None and draft.price_parsed > 0
        has_location = bool(draft.location_raw and draft.location_raw.strip())
        if not has_price and not has_location:
            reasons.append("missing both price and location")
        if not draft.images_raw:
            reasons.append("no images")
        return (len(reasons) == 0, reasons)

    # Convenience: subclasses can keep a `scrape()`-style entrypoint that the
    # orchestrator calls. Default implementation just delegates to
    # fetch_listings so legacy callers keep working during the transition.
    def scrape(self, max_pages: int | None = None) -> list[RawListingDraft]:
        return self.fetch_listings(max_pages=max_pages)