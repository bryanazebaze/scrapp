"""Mapiole adapter — dedicated scraper for mapiole.com.

Refactor of the original MapioleScraper onto the SourceAdapter + BaseFetchMixin
framework. Key changes vs the legacy scraper:

- Removes the hard `[:5]` listing cap (mapiole.py:96) and paginates
  `?page=1..N` per the Burp capture (Burp/Mapoile-Arch.txt documents 7 pages).
- Uses BaseFetchMixin for browser headers, jittered delays, session reuse,
  retries, robots.txt — instead of bare `requests.get` with the default
  python-requests User-Agent (mapiole.py:89) and a fixed 1s sleep.
- Extracts the additional fields the Burp doc documents but the old scraper
  missed: rooms/baths/area (div.ab-keyfact), GPS lat/lng (Leaflet script),
  amenities (div.ab-amenity), property_id (input[name="product_id"]).
- Stores the ORIGINAL image URLs in images_raw (the old scraper kept only
  the local cache paths, losing the source of truth).
- Returns RawListingDraft (dataclass), not ORM models — persistence is owned
  by the ingest pipeline.

Selectors come from Burp/Mapoile-Arch.txt and Burp/Mapoile.txt.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import SourceAdapter
from .drafts import RawListingDraft
from .http_mixin import BaseFetchMixin
from . import utils


class MapioleAdapter(SourceAdapter, BaseFetchMixin):
    platform_slug = "mapiole"
    base_url = "https://mapiole.com"
    adapter_kind = "dedicated"

    # Listing index page. The Burp capture shows pagination via ?page=N.
    CATALOG_URL = "https://mapiole.com/product-listing"
    # Card title link selector (kept from the legacy scraper).
    CARD_LINK_SELECTOR = "a.prop-card__title"
    PAGINATION_SELECTOR = "ul.pagination a.page-link"

    def __init__(self, source_id: Optional[int] = None,
                 crawl_config: dict | None = None) -> None:
        super().__init__(source_id=source_id)
        self.init_fetch(base_url=self.base_url, crawl_config=crawl_config)

    # ----- listing discovery -----
    def fetch_listings(self, max_pages: int | None = None,
                       max_workers: int = 8) -> list[RawListingDraft]:
        """Fetch catalog pages sequentially, then crawl detail pages
        concurrently with a thread pool. `max_workers` controls per-page
        parallelism (8 is a safe default for most real-estate sites)."""
        drafts: list[RawListingDraft] = []
        pages = max_pages or 10  # sane default; Burp shows ~7 pages
        for page in range(1, pages + 1):
            url = f"{self.CATALOG_URL}?page={page}"
            html = self.fetch_text(url, referer=self.base_url)
            if not html:
                break
            soup = BeautifulSoup(html, "html.parser")
            links = soup.select(self.CARD_LINK_SELECTOR)
            if not links:
                # No more cards → end of catalog.
                break
            detail_urls = [
                urljoin(self.base_url, a.get("href"))
                for a in links if a.get("href")
            ]
            # Fetch detail pages concurrently — I/O bound, safe with
            # requests.Session (urllib3 pool is thread-safe, cookie jar has
            # its own lock, headers are read-only after init).
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(self.fetch_details, u): u
                           for u in detail_urls}
                for future in as_completed(futures):
                    u = futures[future]
                    try:
                        draft = future.result()
                    except Exception as e:
                        print(f"[mapiole] error fetching {u}: {e}")
                        continue
                    if draft is not None:
                        drafts.append(draft)
            # Stop if this page had no next-page link.
            next_page = soup.select_one(f'a.page-link[href*="page={page+1}"]')
            if not next_page:
                break
        print(f"[mapiole] fetched {len(drafts)} listings across pages "
              f"({max_workers} workers)")
        return drafts

    # ----- detail extraction -----
    def fetch_details(self, listing_url: str) -> Optional[RawListingDraft]:
        html = self.fetch_text(listing_url, referer=self.CATALOG_URL)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        raw = self._extract_raw(soup, listing_url)
        return self.normalize_data(raw)

    def _extract_raw(self, soup: BeautifulSoup, url: str) -> dict:
        """Extract every field Mapiole exposes on a detail page."""
        title_el = soup.select_one("h1.ab-title")
        title = title_el.get_text(strip=True) if title_el else ""

        price_raw = ""
        price_el = soup.select_one("div.ab-sidebar-price")
        if price_el:
            price_raw = price_el.get_text(" ", strip=True)
        # Hidden raw numeric price (Burp: span#abPrice).
        ab_price = soup.select_one("span#abPrice")
        if ab_price and ab_price.get_text(strip=True).isdigit():
            price_raw = price_raw or ab_price.get_text(strip=True)

        # Location: div.ab-subtitle > a
        loc = ""
        subtitle = soup.select_one("div.ab-subtitle")
        if subtitle:
            a = subtitle.find("a")
            loc = a.get_text(strip=True) if a else subtitle.get_text(strip=True)

        # Description (filtered of boilerplate, as in the legacy scraper).
        desc_parts = []
        banned = [
            "FCFA", "mensuel", "Carrefour ngousso", "Center city",
            "Dites-moi", "Télécharger", "Assistance", "en direct",
            "client entièrement gratuite", "+237", "Non spécifié",
            "Aucun avis", "Vous ne serez pas encore facturé", "Total:",
            "Cameroon", "Suivez-nous", "Restez à jour", "Recherche populaire",
            "Liens rapides", "© Mapiole", "Mapiole.com",
        ]
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if len(t) > 10 and not any(b in t for b in banned):
                desc_parts.append(t)
        description = "\n".join(desc_parts)

        # Key facts (rooms / baths / surface / land).
        bedrooms = bathrooms = None
        area_sqm = None
        for kf in soup.select("div.ab-keyfact"):
            label_el = kf.select_one("span.ab-keyfact-label")
            value_el = kf.select_one("span.ab-keyfact-value")
            if not label_el or not value_el:
                continue
            label = label_el.get_text(strip=True).lower()
            value = value_el.get_text(strip=True)
            if "chambre" in label or "bedroom" in label:
                bedrooms = utils.parse_price(value, min_value=1)
            elif ("douche" in label or "bath" in label or "salle de bain" in label
                  or "sdb" in label or "wc" in label or "bains" in label
                  or "sanitaire" in label):
                bathrooms = utils.parse_price(value, min_value=1)
            elif "surface" in label or "area" in label or "m²" in label or "m2" in label:
                area_sqm = utils.parse_price(value, min_value=1)

        # GPS from Leaflet inline script (Burp: var lat = ...; var lng = ...;).
        lat = lng = None
        for script in soup.find_all("script"):
            txt = script.string or ""
            m_lat = re.search(r"var\s+lat\s*=\s*(-?[\d.]+)", txt)
            m_lng = re.search(r"var\s+lng\s*=\s*(-?[\d.]+)", txt)
            if m_lat and m_lng:
                lat = float(m_lat.group(1))
                lng = float(m_lng.group(1))
                break

        # Amenities.
        amenities = [a.get_text(strip=True) for a in soup.select("div.ab-amenity")
                     if a.get_text(strip=True)]

        # property_id (Burp: input[name="product_id"]).
        property_id = None
        pid_input = soup.select_one('input[name="product_id"]')
        if pid_input:
            property_id = pid_input.get("value")

        # Images — original URLs from the gallery (canonical record).
        images: list[str] = []
        for img in soup.select(".ab-gallery img, .ab-gallery-grid img, .ab-gallery-banner img"):
            src = img.get("src") or img.get("data-src")
            if src:
                full = src if src.startswith("http") else urljoin(self.base_url, src)
                if utils.is_real_image(full):
                    images.append(full)

        return {
            "url": url,
            "title": title,
            "price_raw": price_raw,
            "location": loc,
            "description": description,
            "images": images,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "area_sqm": area_sqm,
            "lat": lat,
            "lng": lng,
            "amenities": amenities,
            "property_id": property_id,
        }

    # ----- normalization -----
    def normalize_data(self, raw: dict) -> RawListingDraft:
        title = raw.get("title") or "Non renseigné"
        price_raw = raw.get("price_raw") or ""
        price_parsed = utils.parse_price(price_raw, min_value=1000,
                                         reject_per_sqm=True)
        images_raw = raw.get("images") or []
        type_raw = utils.classify_property_type(
            f"{title} {raw.get('url','')} {raw.get('description','')}"
        )
        return RawListingDraft(
            url_source=raw.get("url", ""),
            title_raw=title,
            price_raw=price_raw or None,
            price_parsed=price_parsed,
            currency="XAF",
            location_raw=raw.get("location") or None,
            description_raw=raw.get("description") or None,
            property_type_raw=type_raw,
            images_raw=images_raw,
            bedrooms=raw.get("bedrooms"),
            bathrooms=raw.get("bathrooms"),
            area_sqm=raw.get("area_sqm"),
            latitude=raw.get("lat"),
            longitude=raw.get("lng"),
            amenities=raw.get("amenities") or [],
            confidence=1.0,
            payload={
                **{k: v for k, v in raw.items() if k != "images"},
                "nom_plateforme": "Mapiole",
            },
        )


# Backward-compatible alias for any legacy imports.
MapioleScraper = MapioleAdapter