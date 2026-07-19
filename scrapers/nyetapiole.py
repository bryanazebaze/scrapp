"""Nyetapiole adapter -- dedicated scraper for nyetapiole.com (JSON API).

Unlike Mapiole (HTML scraping) and Kasastay (Next.js JSON route probing),
Nyetapiole exposes a clean REST API that returns structured JSON. The list
endpoint (``/api/v1/listing/articles``) already contains all listing fields
-- title, price, description, rooms, bedrooms, bathrooms, images, tags,
category, district, city -- so no detail-page round-trip is needed. The
detail endpoint (``/api/v1/listing/article/{slug}``) returns the same schema
and is only used by ``fetch_details`` for single-URL lookups.

Key normalization decisions (verified against the live API on 2026-07-16):

- ``price`` is already an integer in XAF. We pass it directly to
  ``price_parsed`` and set ``price_raw`` to ``str(price)``.
- ``surface`` is ``0`` on every listing sampled (Nyapiole does not collect
  area). We convert ``0`` → ``None`` so the ingest pipeline does not store
  a bogus 0 sqm value.
- ``latitude`` / ``longitude`` are ``0`` or ``null`` when the landlord did
  not drop a pin. We convert both to ``None`` so the location resolver
  falls back to neighborhood-based coordinates from ``utils.py``.
- ``bedrooms`` / ``bathrooms`` are ``0`` when unspecified. We convert ``0``
  → ``None`` to avoid polluting the canonical record with phantom rooms.
- ``tags`` (e.g. "Meublé", "Climatisation", "Parking couvert") map directly
  to ``amenities``.
- ``category.name`` ("Studio", "Appartement", "Villa", "Maison", "Chambre")
  is passed through ``utils.classify_property_type`` so "Villa" → "Maison"
  and "Studio" → "Appartement", matching the rest of the platform.
- ``url_source`` is the web property page (``/property/{slug}``), not the
  API endpoint, so dedup hashing is stable against API version changes.
- The API requires ``Accept: application/json`` and a ``Referer`` header or
  it returns 422. We override the session ``Accept`` in ``__init__`` and
  pass ``referer=.../search`` on every request.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from .base import SourceAdapter
from .drafts import RawListingDraft
from .http_mixin import BaseFetchMixin
from . import utils


class NyetapioleAdapter(SourceAdapter, BaseFetchMixin):
    platform_slug = "nyetapiole"
    base_url = "https://nyetapiole.com"
    adapter_kind = "dedicated"

    # --- API endpoints ---
    API_BASE = "https://nyetapiole.com/api/v1/listing"
    LIST_ENDPOINT = f"{API_BASE}/articles"
    DETAIL_ENDPOINT = f"{API_BASE}/article"
    WEB_PROPERTY_BASE = "https://nyetapiole.com/property"

    # Query params from the Burp capture (Nyetapoile.txt). Empty values are
    # required by the server -- omitting them returns 422.
    LIST_PARAMS_TEMPLATE = (
        "q=&status=&sort=&page={page}&per_page={per_page}"
        "&transactionType=all&propertyTypes=&priceMin=&priceMax="
        "&surfaceMin=&surfaceMax=&rooms=&location="
        "&features=&energyRatings="
    )

    def __init__(self, source_id: Optional[int] = None,
                 crawl_config: dict | None = None) -> None:
        super().__init__(source_id=source_id)
        self.init_fetch(base_url=self.base_url, crawl_config=crawl_config)
        # The API returns 422 without Accept: application/json.
        self.session.headers["Accept"] = "application/json"

    # ----- listing discovery -----
    def fetch_listings(self, max_pages: int | None = None,
                       max_workers: int = 8) -> list[RawListingDraft]:
        """Paginate the JSON list endpoint. No detail-page round-trips
        needed -- the list response already contains all fields."""
        drafts: list[RawListingDraft] = []
        pages = max_pages or 10
        per_page = 12  # server default, do not exceed
        referer = f"{self.base_url}/search"
        for page in range(1, pages + 1):
            qs = self.LIST_PARAMS_TEMPLATE.format(page=page, per_page=per_page)
            url = f"{self.LIST_ENDPOINT}?{qs}"
            resp = self.fetch(url, referer=referer)
            if resp is None or resp.status_code >= 400:
                print(f"[nyetapiole] stopping at page {page} "
                      f"(status={resp.status_code if resp else 'None'})")
                break
            try:
                payload = resp.json()
            except json.JSONDecodeError:
                print(f"[nyetapiole] page {page}: invalid JSON, stopping")
                break
            items = payload.get("data", {}).get("list", [])
            if not items:
                print(f"[nyetapiole] page {page}: empty list, stopping")
                break
            for item in items:
                draft = self.normalize_data(item)
                if draft:
                    drafts.append(draft)
            print(f"[nyetapiole] page {page}: {len(items)} listings")
        print(f"[nyetapiole] fetched {len(drafts)} listings total")
        return drafts

    # ----- detail extraction (single URL) -----
    def fetch_details(self, listing_url: str) -> Optional[RawListingDraft]:
        """Fetch a single listing by its web URL (``/property/{slug}``) or
        bare slug. Calls the detail API endpoint."""
        slug = self._extract_slug(listing_url)
        if not slug:
            return None
        api_url = f"{self.DETAIL_ENDPOINT}/{slug}"
        resp = self.fetch(api_url, referer=f"{self.WEB_PROPERTY_BASE}/{slug}")
        if resp is None or resp.status_code >= 400:
            return None
        try:
            data = resp.json().get("data", {})
        except json.JSONDecodeError:
            return None
        return self.normalize_data(data)

    @staticmethod
    def _extract_slug(url: str) -> str | None:
        """Extract the slug from either a web URL, an API URL, or a bare
        slug string."""
        if not url:
            return None
        # Strip trailing slash and take the last path segment.
        path = url.rstrip("/").split("/")[-1]
        return path if path else None

    # ----- normalization -----
    def normalize_data(self, raw: dict[str, Any]) -> RawListingDraft | None:
        """Map a Nyetapiole JSON listing to a ``RawListingDraft``.

        Returns ``None`` if the listing has no slug or no title (unusable).
        """
        if not raw or not isinstance(raw, dict):
            return None

        slug = raw.get("slug")
        title = raw.get("title", "").strip()
        if not slug or not title:
            return None

        # --- URL (web property page, not the API endpoint) ---
        url_source = f"{self.WEB_PROPERTY_BASE}/{slug}"

        # --- Price (already int, in XAF) ---
        price = raw.get("price")
        price_parsed = int(price) if isinstance(price, (int, float)) and price > 0 else None
        price_raw = str(price) if price is not None else None

        # --- Location ---
        district = raw.get("district") or {}
        city_obj = district.get("city") or {}
        district_name = district.get("name", "")
        city_name = city_obj.get("name", "")
        # Build "District, City" for location_raw (matches Mapiole/Kasastay format)
        if district_name and city_name:
            location_raw = f"{district_name}, {city_name}"
        elif city_name:
            location_raw = city_name
        elif district_name:
            location_raw = district_name
        else:
            location_raw = None

        # --- Coordinates (0 / null → None) ---
        lat = raw.get("latitude")
        lng = raw.get("longitude")
        latitude = float(lat) if isinstance(lat, (int, float)) and lat != 0 else None
        longitude = float(lng) if isinstance(lng, (int, float)) and lng != 0 else None

        # --- Rooms (0 → None) ---
        bedrooms = raw.get("bedrooms")
        bathrooms = raw.get("bathrooms")
        bedrooms = bedrooms if isinstance(bedrooms, int) and bedrooms > 0 else None
        bathrooms = bathrooms if isinstance(bathrooms, int) and bathrooms > 0 else None

        # --- Surface (0 → None; Nyetapiole doesn't collect this) ---
        surface = raw.get("surface")
        area_sqm = float(surface) if isinstance(surface, (int, float)) and surface > 0 else None

        # --- Description (clean \r\n) ---
        description = raw.get("description") or ""
        if isinstance(description, str):
            description = description.replace("\r\n", "\n").replace("\r", "\n").strip()

        # --- Images (extract URLs from medias array) ---
        images: list[str] = []
        for media in (raw.get("medias") or raw.get("images") or []):
            if isinstance(media, dict):
                img_url = media.get("url")
                if img_url and utils.is_real_image(img_url):
                    images.append(img_url)

        # --- Tags → amenities ---
        amenities: list[str] = []
        for tag in (raw.get("tags") or []):
            if isinstance(tag, dict):
                tag_name = tag.get("name")
                if tag_name:
                    amenities.append(tag_name)

        # --- Property type (classify from category + title) ---
        category = raw.get("category") or {}
        category_name = category.get("name", "")
        # classify_property_type maps "Villa" → "Maison", "Studio" → "Appartement"
        type_raw = utils.classify_property_type(
            f"{category_name} {title} {raw.get('description', '')}"
        )

        # --- Transaction type (Location = rental, Vente = sale) ---
        tx_type = (raw.get("type") or {}).get("name", "")
        periodicity = (raw.get("periodicity") or {}).get("name", "")

        return RawListingDraft(
            url_source=url_source,
            title_raw=title,
            price_raw=price_raw,
            price_parsed=price_parsed,
            currency="XAF",
            location_raw=location_raw,
            description_raw=description or None,
            property_type_raw=type_raw,
            images_raw=images,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            area_sqm=area_sqm,
            latitude=latitude,
            longitude=longitude,
            amenities=amenities,
            confidence=1.0,  # dedicated adapter → always auto-promoted
            payload={
                "nom_plateforme": "Nyetapiole",
                "nyetapiole_id": raw.get("id"),
                "nyetapiole_slug": slug,
                "category_raw": category_name,
                "transaction_type": tx_type,
                "periodicity": periodicity,
                "access_fees": raw.get("access_fees"),
                "visit_fees": raw.get("visit_fees"),
                "pub_date": raw.get("pub_date"),
                "views": raw.get("views"),
                "stars": raw.get("stars"),
                "living_rooms": raw.get("living_rooms"),
                "landlord_type": (raw.get("user") or {}).get("account_type"),
            },
        )


# Backward-compatible alias.
NyetapioleScraper = NyetapioleAdapter