"""Kasastay adapter — dedicated scraper for kasastay.com (Next.js).

Refactor of the legacy KasastayScraper onto SourceAdapter + BaseFetchMixin.
Key changes:

- Removes the hard `[:5]` cap (kasastay.py:110) and paginates via `?page=N`
  / `rel="next"`.
- Uses BaseFetchMixin for hardened HTTP (browser headers, jittered delays,
  session reuse, retries, robots.txt) instead of bare `requests.get`
  (kasastay.py:104) with the default User-Agent.
- Adds a `_next/data/{buildId}/...` JSON probe: Next.js apps expose the same
  page data as JSON at that route. The buildId is extracted from the
  `__NEXT_DATA__` script tag. If the probe returns JSON, we consume it
  (richer, more stable than HTML); otherwise we fall back to HTML parsing.
- Stores ORIGINAL image URLs in images_raw (decoded from the `_next/image`
  proxy per the legacy kasastay.py:79-82 logic, now in utils.decode_next_image_url).
- Extracts rooms/baths/area when present in the Next.js page props or HTML.

No Burp capture of Kasastay exists (Burp/Kassastay.txt is only 3 lines), so
the JSON route shape is inferred from the standard Next.js convention and
verified at runtime with a graceful HTML fallback. A follow-up Burp capture
of Kasastay is flagged in docs/burp-analysis.md.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlsplit

from bs4 import BeautifulSoup

from .base import SourceAdapter
from .drafts import RawListingDraft
from .http_mixin import BaseFetchMixin
from . import utils


def _scan_count(text: str, pattern: str) -> int | None:
    """Extract a small integer (1-50) from `text` matching `pattern`. Used
    for bedrooms/bathrooms in the Kasastay HTML fallback where structured
    fields aren't available."""
    for m in re.finditer(pattern, text, re.IGNORECASE):
        try:
            v = int(m.group(1))
        except (ValueError, IndexError):
            continue
        if 1 <= v <= 50:
            return v
    return None


class KasastayAdapter(SourceAdapter, BaseFetchMixin):
    platform_slug = "kasastay"
    base_url = "https://kasastay.com"
    adapter_kind = "dedicated"

    CATALOG_URL = "https://kasastay.com/fr/property/search?business=LongStay"
    CARD_LINK_SELECTOR = "a.group.flex.h-full.flex-col"
    # The buildId is discovered at runtime from __NEXT_DATA__.

    def __init__(self, source_id: Optional[int] = None,
                 crawl_config: dict | None = None) -> None:
        super().__init__(source_id=source_id)
        self.init_fetch(base_url=self.base_url, crawl_config=crawl_config)
        self._build_id: str | None = None

    # ----- Next.js buildId discovery -----
    def _discover_build_id(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return None
        try:
            data = json.loads(script.string)
            return data.get("buildId")
        except Exception:
            return None

    def _try_next_data(self, page_url: str) -> dict | None:
        """Probe Next.js `_next/data/{buildId}/{page}.json`. Returns the
        `pageProps` dict or None if unavailable / not JSON."""
        if not self._build_id:
            return None
        path = urlparse(page_url).path.strip("/")
        if not path:
            return None
        data_url = f"{self.base_url}/_next/data/{self._build_id}/{path}.json"
        resp = self.fetch(data_url, referer=page_url)
        if resp is None or resp.status_code >= 400:
            return None
        try:
            payload = resp.json()
            return payload.get("pageProps") or payload
        except Exception:
            return None

    # ----- listing discovery -----
    def fetch_listings(self, max_pages: int | None = None,
                       max_workers: int = 8) -> list[RawListingDraft]:
        """Fetch catalog pages sequentially, then crawl detail pages
        concurrently with a thread pool."""
        drafts: list[RawListingDraft] = []
        pages = max_pages or 10
        url = self.CATALOG_URL
        for page in range(1, pages + 1):
            page_url = f"{self.CATALOG_URL}&page={page}" if page > 1 else self.CATALOG_URL
            html = self.fetch_text(page_url, referer=self.base_url)
            if not html:
                break
            if page == 1 and not self._build_id:
                self._build_id = self._discover_build_id(html)
            soup = BeautifulSoup(html, "html.parser")
            links = soup.select(self.CARD_LINK_SELECTOR)
            if not links:
                # Try JSON route before giving up.
                props = self._try_next_data(page_url)
                if props:
                    drafts.extend(self._drafts_from_next_props(props))
                    break
                break
            detail_urls = [
                urljoin(self.base_url, a.get("href"))
                for a in links if a.get("href")
            ]
            # Fetch detail pages concurrently.
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(self.fetch_details, u): u
                           for u in detail_urls}
                for future in as_completed(futures):
                    u = futures[future]
                    try:
                        draft = future.result()
                    except Exception as e:
                        print(f"[kasastay] error fetching {u}: {e}")
                        continue
                    if draft is not None:
                        drafts.append(draft)
            # Next page link.
            nxt = soup.find("a", attrs={"rel": "next"})
            if not nxt and not soup.select_one(f'a[href*="page={page+1}"]'):
                break
        print(f"[kasastay] fetched {len(drafts)} listings ({max_workers} workers)")
        return drafts

    # Substrings that indicate boilerplate, not a real listing description.
    _DESC_BANNED = [
        "Newsletter mensuelle",
        "Devenir hôte",
        "Rentabilisez votre logement",
        "Trouvez votre logement idéal au Cameroun",
        "Copyright©",
        "Tous droits réservés",
        "Pas encore d'avis",
        "soyez le premier à séjourner",
        "Planifier une visite",
        "Choisissez une date",
        "l'hôte confirmera votre visite",
        "D'autres logements",
        "Hôte vérifié",
        "Hote verifie",
    ]

    @staticmethod
    def _clean_description(text: str) -> str:
        """Remove boilerplate lines from a description string (newline-
        separated). Used by both the HTML fallback and the JSON path."""
        if not text:
            return text
        kept = []
        for line in text.split("\n"):
            t = line.strip()
            if len(t) <= 10:
                continue
            if any(b in t for b in KasastayAdapter._DESC_BANNED):
                continue
            if "Cameroun, Wouri" in t or "Cameroun, Mfoundi" in t:
                continue
            kept.append(t)
        return "\n".join(kept)

    def _drafts_from_next_props(self, props: dict) -> list[RawListingDraft]:
        """Best-effort extraction from Next.js pageProps JSON."""
        out = []
        items = props.get("properties") or props.get("listings") or []
        if isinstance(items, dict):
            items = items.get("data") or items.get("items") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            raw = {
                "url": urljoin(self.base_url, item.get("slug") or item.get("url") or ""),
                "title": item.get("title") or item.get("name") or "",
                "price_raw": str(item.get("price") or item.get("amount") or ""),
                "location": item.get("location") or item.get("city") or "",
                "description": self._clean_description(item.get("description") or ""),
                "images": item.get("images") or item.get("photos") or [],
                "bedrooms": item.get("bedrooms") or item.get("rooms"),
                "bathrooms": item.get("bathrooms") or item.get("baths"),
                "area_sqm": item.get("area") or item.get("surface"),
                "lat": item.get("lat") or item.get("latitude"),
                "lng": item.get("lng") or item.get("longitude"),
                "amenities": item.get("amenities") or [],
                "property_id": item.get("id"),
            }
            out.append(self.normalize_data(raw))
        return out

    # ----- detail extraction -----
    def fetch_details(self, listing_url: str) -> Optional[RawListingDraft]:
        # Prefer JSON if available.
        props = self._try_next_data(listing_url)
        if props:
            drafts = self._drafts_from_next_props(props)
            if drafts:
                return drafts[0]
        # HTML fallback.
        html = self.fetch_text(listing_url, referer=self.CATALOG_URL)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        return self.normalize_data(self._extract_raw(soup, listing_url))

    def _extract_raw(self, soup: BeautifulSoup, url: str) -> dict:
        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else "Appartement Kasastay"

        # Price: search for visible text containing "XAF" (not inside script/style).
        price_raw = ""
        for el in soup.find_all(string=re.compile("XAF|FCFA|CFA")):
            if el.parent and el.parent.name in ("script", "style", "noscript"):
                continue
            price_raw = el.strip()
            break

        # Description (filtered of boilerplate — Kasastay pages repeat the
        # same navigation/footer/marketing text across all listings).
        desc_parts = []
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if len(t) <= 10:
                continue
            if any(b in t for b in self._DESC_BANNED):
                continue
            # Skip nearby-location suggestion strings.
            if "Cameroun, Wouri" in t or "Cameroun, Mfoundi" in t:
                continue
            desc_parts.append(t)
        description = "\n".join(desc_parts)

        # Images: decode _next/image proxy URLs (utils.decode_next_image_url).
        images: list[str] = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue
            real = utils.decode_next_image_url(src, self.base_url)
            if real and utils.is_real_image(real):
                images.append(real)

        # Location: og:description first, then city scan, then og:title, then
        # the h1 title (often "Appartement ... à [neighborhood]"). Do NOT
        # default to "Cameroun" — that country-level string never resolves to
        # a city and leaves 82% of canonicals with NULL location_id. Leaving
        # None lets the resolver try neighborhood-based city inference cleanly.
        location = ""
        meta_desc = soup.find("meta", {"property": "og:description"})
        if meta_desc and meta_desc.get("content"):
            location = meta_desc["content"].strip()[:80]
        if not location:
            location = utils.detect_city_text(soup) or ""
        if not location:
            meta_title = soup.find("meta", {"property": "og:title"})
            if meta_title and meta_title.get("content"):
                location = meta_title["content"].strip()[:80]
        if not location and title:
            location = title

        # Bedrooms / bathrooms / area: Next.js HTML fallback doesn't expose
        # these in stable structured elements, so scan the page text for
        # common French real-estate patterns ("2 chambres", "1 douche", "50 m²").
        page_text = soup.get_text(" ", strip=True)
        bedrooms = _scan_count(page_text, r"(\d+)\s*(?:chambre|bedroom|piece|pièce)")
        bathrooms = _scan_count(page_text, r"(\d+)\s*(?:douche|bath|salle\s*de\s*bain|sdb|wc|toilette)")
        area_sqm = None
        m = re.search(r"(\d[\d\s.,]*)\s*m[²2]", page_text)
        if m:
            parsed = utils.parse_price(m.group(1), min_value=1)
            if parsed and 5 <= parsed <= 50000:
                area_sqm = float(parsed)

        return {
            "url": url,
            "title": title,
            "price_raw": price_raw,
            "location": location,
            "description": description,
            "images": images,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "area_sqm": area_sqm,
            "lat": None,
            "lng": None,
            "amenities": [],
            "property_id": None,
        }

    def normalize_data(self, raw: dict) -> RawListingDraft:
        title = raw.get("title") or "Appartement Kasastay"
        price_raw = raw.get("price_raw") or ""
        price_parsed = utils.parse_price(price_raw, min_value=1000,
                                         reject_per_sqm=True)
        images_raw = [u for u in (raw.get("images") or []) if isinstance(u, str)]
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
                "nom_plateforme": "Kasastay",
            },
        )


# Backward-compatible alias.
KasastayScraper = KasastayAdapter