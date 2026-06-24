"""Universal fallback scraper.

Given an arbitrary real-estate URL, discovers listing pages, detects
property cards heuristically, extracts fields (JSON-LD -> OpenGraph ->
heuristic), scores confidence, and produces RawListingDrafts. Low-confidence
listings land in raw_listings with review_status='pending' for human review
before promotion to a canonical property (see core.ingest).

This is the secondary system; dedicated adapters (Mapiole, Kasastay) handle
the known sources. The universal adapter exists so a new site can be onboarded
in minutes, before a dedicated scraper is written.

Pipeline:
  1. URL discovery   — candidate listing-page links + pagination + sitemap.
  2. Card detection  — repeated DOM structures that look like property cards
                       (3-of-5 signals: repeated signature, img, detail link,
                       price text, city keyword).
  3. Field extraction — extractors.extract_all (JSON-LD > OG > heuristic).
  4. Confidence      — confidence.compute_confidence; gated by ingest.
"""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from .base import SourceAdapter
from .drafts import RawListingDraft
from .http_mixin import BaseFetchMixin
from . import utils
from . import extractors
from . import confidence


# Listing-page URL patterns (path segments that suggest a property listing).
LISTING_PATH_RE = re.compile(
    r"/(property|properties|listing|listings|annonce|annonces|detail|details"
    r"|for-rent|for-sale|immobilier|real-estate|product-listing|search)",
    re.IGNORECASE,
)
# Utility/nav paths that are NEVER property details — used to filter out
# non-card links. Detail URLs are identified by card structure + signals,
# not by a rigid path pattern (Mapiole uses /City/Type/Title-ID, etc.).
UTILITY_PATH_RE = re.compile(
    r"/(login|register|signin|signup|contact|about|blog|search|admin|account"
    r"|cart|wishlist|favorites|api|legal|privacy|terms|help|faq)",
    re.IGNORECASE,
)
_PRICE_TEXT_RE = re.compile(
    r"(XAF|FCFA|CFA)[\s\d.,]{4,}|[\d][\d\s.,]{4,}\s*(XAF|FCFA|CFA)",
    re.IGNORECASE,
)


class UniversalAdapter(SourceAdapter, BaseFetchMixin):
    platform_slug = "universal"
    adapter_kind = "universal"

    def __init__(self, source_id: Optional[int] = None,
                 crawl_config: dict | None = None,
                 seed_url: str = "") -> None:
        super().__init__(source_id=source_id)
        self.seed_url = seed_url or (crawl_config or {}).get("seed_url", "")
        self.base_url = self._derive_base_url(self.seed_url)
        self.init_fetch(base_url=self.base_url, crawl_config=crawl_config)

    @staticmethod
    def _derive_base_url(url: str) -> str:
        if not url:
            return ""
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    # ----- Stage 1: URL discovery -----
    def discover_listing_pages(self, max_pages: int = 20) -> list[str]:
        """Find candidate listing/index pages from the seed URL."""
        if not self.seed_url:
            return []
        pages: list[str] = []
        seen: set[str] = set()

        def add(u: str) -> None:
            if u and u not in seen:
                seen.add(u)
                pages.append(u)

        # Seed itself may already be a listing page.
        add(self.seed_url)
        html = self.fetch_text(self.seed_url, referer=self.base_url)
        if not html:
            return pages
        soup = BeautifulSoup(html, "html.parser")

        # sitemap.xml
        sitemap_url = urljoin(self.base_url, "/sitemap.xml")
        sm = self.fetch_text(sitemap_url)
        if sm:
            for m in re.finditer(r"<loc>([^<]+)</loc>", sm):
                loc = m.group(1).strip()
                if LISTING_PATH_RE.search(loc):
                    add(loc)

        # Links that look like listing pages.
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(self.base_url, href)
            if LISTING_PATH_RE.search(urlparse(full).path):
                add(full)

        # Pagination: ?page=N, /page/N, rel="next".
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"[?&]page=\d+", href) or re.search(r"/page/\d+", href):
                add(urljoin(self.base_url, href))
        nxt = soup.find("a", attrs={"rel": "next"})
        if nxt and nxt.get("href"):
            add(urljoin(self.base_url, nxt["href"]))

        # Only keep listing-page-like URLs (drop obvious detail pages from the
        # index set). We can't perfectly distinguish index vs detail by path,
        # so we keep URLs that match the listing pattern OR have pagination.
        index_pages = [u for u in pages if LISTING_PATH_RE.search(urlparse(u).path)
                       or re.search(r"[?&]page=\d+|/page/\d+", urlparse(u).path)]
        # Always keep the seed itself even if it doesn't match.
        if self.seed_url and self.seed_url not in index_pages:
            index_pages.insert(0, self.seed_url)
        return index_pages[:max_pages]

    # ----- Stage 2: card detection -----
    def detect_cards(self, soup: BeautifulSoup) -> list[str]:
        """Detect property-card containers and return their detail URLs.

        Heuristic: group <a> anchors by their parent container's tag+class
        signature. Signatures appearing >= 3 times indicate a listing grid.
        Each candidate card is then validated by a 3-of-5 signal test (image,
        detail link, price text, city keyword, repeated signature). We do NOT
        require a rigid detail-URL path pattern — different sites use
        /City/Type/Title-ID (Mapiole), /property/slug (Kasastay), etc. — so
        the link's presence plus the structural repetition is the signal.
        """
        from collections import defaultdict
        candidates_by_sig: dict[str, list[tuple]] = defaultdict(list)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href or href.startswith("#"):
                continue
            full = urljoin(self.base_url, href)
            # same-domain only
            if urlparse(full).netloc and urlparse(full).netloc != urlparse(self.base_url).netloc:
                continue
            if UTILITY_PATH_RE.search(urlparse(full).path):
                continue
            parent = a.parent
            if not isinstance(parent, Tag):
                continue
            sig = f"{parent.name}." + ".".join(sorted(parent.get("class", [])))
            candidates_by_sig[sig].append((a, parent, full))

        detail_urls: list[str] = []
        seen: set[str] = set()
        for sig, group in candidates_by_sig.items():
            if len(group) < 3:
                continue  # not a repeated structure
            for a, parent, full in group:
                if full in seen:
                    continue
                if self._looks_like_card(parent):
                    seen.add(full)
                    detail_urls.append(full)
        return detail_urls

    def _looks_like_card(self, container: Tag) -> bool:
        """3-of-5 signal test for a card container."""
        signals = 0
        # 1. has a non-trivial image
        has_img = any(img.get("src") and utils.is_real_image(img.get("src"))
                     for img in container.find_all("img"))
        if has_img:
            signals += 1
        # 2. has a link (any non-utility href)
        has_link = any(a.get("href") and not a["href"].startswith("#")
                       for a in container.find_all("a", href=True))
        if has_link:
            signals += 1
        # 3. price text
        text = container.get_text(" ", strip=True)
        if _PRICE_TEXT_RE.search(text):
            signals += 1
        # 4. Cameroon city keyword
        if utils.detect_city(text):
            signals += 1
        # 5. repeated signature (caller already grouped by signature >= 3)
        signals += 1
        return signals >= 3

    # ----- Stage 3+4: extract + score -----
    def fetch_details(self, listing_url: str, from_card: bool = True) -> Optional[RawListingDraft]:
        html = self.fetch_text(listing_url, referer=self.base_url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        extracted = extractors.extract_all(soup, base_url=self.base_url)
        if not extracted.get("title"):
            return None
        # Verify images are resolvable (HEAD) for the f_images factor.
        images = extracted.get("images") or []
        images_ok = any(self.head_ok(u) for u in images[:3]) if images else False
        score = confidence.compute_confidence(
            extracted, from_card=from_card,
            images_resolvable=images_ok, url_source=listing_url,
        )
        factors = confidence.confidence_factors(
            extracted, from_card=from_card,
            images_resolvable=images_ok, url_source=listing_url,
        )
        return self._to_draft(listing_url, extracted, score, factors)

    def _to_draft(self, url: str, extracted: dict, score: float,
                  factors: dict) -> RawListingDraft:
        title = extracted.get("title") or "Untitled"
        price_raw = extracted.get("price_raw")
        price_parsed = extracted.get("price_parsed")
        images = [u for u in (extracted.get("images") or []) if isinstance(u, str)]
        prop_type = extracted.get("property_type") or utils.classify_property_type(title)
        return RawListingDraft(
            url_source=url,
            title_raw=title,
            price_raw=price_raw,
            price_parsed=price_parsed,
            currency=extracted.get("currency", "XAF"),
            location_raw=extracted.get("location"),
            description_raw=extracted.get("description"),
            property_type_raw=prop_type,
            images_raw=images,
            latitude=extracted.get("lat"),
            longitude=extracted.get("lng"),
            confidence=score,
            payload={
                "extraction_factors": factors,
                "extraction_sources": extracted.get("_source", {}),
                "nom_plateforme": "universal",
            },
        )

    # ----- orchestration -----
    def fetch_listings(self, max_pages: int | None = None) -> list[RawListingDraft]:
        drafts: list[RawListingDraft] = []
        pages = self.discover_listing_pages(max_pages=max_pages or 20)
        if not pages:
            return drafts
        for page_url in pages:
            html = self.fetch_text(page_url, referer=self.base_url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            card_urls = self.detect_cards(soup)
            if not card_urls:
                continue
            for detail_url in card_urls:
                draft = self.fetch_details(detail_url, from_card=True)
                if draft is not None:
                    drafts.append(draft)
                self._polite_sleep()
        print(f"[universal] {self.seed_url} -> {len(drafts)} drafts "
              f"(avg confidence {sum(d.confidence for d in drafts)/max(len(drafts),1):.2f})")
        return drafts

    def normalize_data(self, raw: dict) -> RawListingDraft:
        # Universal extracts already produce the canonical fields; this is a
        # no-op pass for interface compliance.
        return RawListingDraft(
            url_source=raw.get("url", ""),
            title_raw=raw.get("title", "Untitled"),
            price_raw=raw.get("price_raw"),
            price_parsed=raw.get("price_parsed"),
            location_raw=raw.get("location"),
            description_raw=raw.get("description"),
            property_type_raw=raw.get("property_type"),
            images_raw=raw.get("images") or [],
            confidence=raw.get("confidence", 0.0),
            payload=raw.get("payload", {}),
        )