"""
AI-powered scraper using Qwen 3.6 Flash to intelligently analyze real-estate sites.

Instead of hardcoded heuristics, the AI inspects each page, discovers the
DOM structure (cards, detail URLs, pagination), then extracts fields.
This handles any site that a human could manually parse.

Flow:
  1. Fetch listing/index page
  2. AI analyzes structure → card selectors, URL patterns, pagination
  3. Extract listing detail URLs using discovered selectors
  4. For each detail page, AI extracts property fields → RawListingDraft
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from openai import OpenAI

from .base import SourceAdapter
from .drafts import RawListingDraft
from .http_mixin import BaseFetchMixin

# --------------------------------------------------------------------------- #
# HTML cleaning — strip noise before sending to AI
# --------------------------------------------------------------------------- #
_CLEAN_TAGS = ["script", "style", "noscript", "iframe", "svg", "path", "link", "meta"]
_CLEAN_ATTRS = ["style", "onclick", "onload", "onerror", "data-*", "aria-*"]


def _clean_html(soup: BeautifulSoup) -> str:
    """Strip scripts, styles, and useless attributes; keep DOM skeleton."""
    for tag in soup.find_all(_CLEAN_TAGS):
        tag.decompose()
    for tag in soup.find_all(True):
        # Remove verbose attributes
        for attr in list(tag.attrs):
            if attr in _CLEAN_ATTRS or attr.startswith("data-") or attr.startswith("aria-"):
                del tag[attr]
    # Truncate to ~60k chars (plenty for structure analysis)
    body = soup.body or soup
    text = str(body)
    if len(text) > 60000:
        text = text[:30000] + text[-30000:]
    return text


def _clean_detail_html(soup: BeautifulSoup) -> str:
    """Light clean for a detail page — keep enough for extraction."""
    for tag in soup.find_all(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    body = soup.body or soup
    text = str(body)
    if len(text) > 40000:
        text = text[:20000] + text[-20000:]
    return text


# --------------------------------------------------------------------------- #
# AI client
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT_STRUCTURE = """You are a web-scraping expert. You receive HTML of a real-estate listing/index page.
Analyze the DOM structure and return ONLY valid JSON (no markdown, no code fences).

Return this JSON shape:
{
  "card_selector": "CSS selector for each property card container (e.g. article.property, div.listing-card). Use a selector that captures ALL repeated cards on the page.",
  "detail_link_selector": "CSS selector to find the <a> tag inside each card that leads to the detail page. Leave empty string if the card itself contains the link.",
  "detail_url_attr": "href",
  "pagination_selector": "CSS selector for pagination links (all page-number or next links). Leave empty string if no pagination found.",
  "next_page_text": "text of the 'next' link if found (e.g. 'Next', 'Suivant', '>', '»'). Leave empty if unclear.",
  "listing_count": <estimated number of property cards visible on this page>,
  "notes": "brief observation about the site structure"
}

Rules:
- Selectors must be REAL selectors that will work with BeautifulSoup's select() method.
- Prefer class-based selectors over structural ones (e.g. "article.property-item" not "div > div > div > a").
- If cards are <article> elements, prefer "article.property" or "article[class*='property']".
- If you can't determine something, use empty string or 0."""

SYSTEM_PROMPT_EXTRACT = """You are a real-estate data extraction expert. You receive HTML of a single property listing detail page.
Extract every available field and return ONLY valid JSON (no markdown, no code fences).

Return this JSON shape:
{
  "title": "full listing title",
  "price_raw": "price as shown on page (e.g. '500.000 FCFA')",
  "price_parsed": <numeric price, integer only, no decimals. Parse '500.000' as 500000, '150 000 FCFA' as 150000>,
  "currency": "XAF" or "CFA" or "EUR" or "USD",
  "location": "city and neighborhood if available",
  "description": "full property description text",
  "property_type": "Appartement" or "Maison" or "Villa" or "Studio" or "Chambre" or "Duplex" or "Triplex" or "Terrain" or "Immeuble" or "Bureau" or "Commercial",
  "bedrooms": <integer or null>,
  "bathrooms": <integer or null>,
  "area_sqm": <integer or null>,
  "images": ["url1", "url2", ...],
  "features": ["pool", "parking", "garden", ...] or [],
  "listing_purpose": "rent" or "sale" or null
}

Rules:
- price_parsed: remove ALL non-digit characters. '500.000' → 500000. '1 200 000 FCFA' → 1200000.
- bedrooms: look for 'chambre(s)', 'bedroom(s)', 'pièce(s)'. A 'studio' is 0 or 1 bedroom.
- If area is in hectares, convert to m² (1 ha = 10000 m²).
- Images: collect ALL image URLs that look like property photos (skip logos, icons, banners).
- If a field is not found, use null or empty array."""


def _ai_call(client: OpenAI, system: str, html: str, model: str = "qwen3.6-flash") -> dict:
    """Single AI call. Returns parsed JSON dict, or {} on failure."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": html},
            ],
            temperature=0.1,
            max_tokens=4096,
            extra_body={"enable_thinking": False},
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"[ai_scraper] AI call failed: {e}")
        return {}


# --------------------------------------------------------------------------- #
# AIScraper adapter
# --------------------------------------------------------------------------- #
class AIScraper(SourceAdapter, BaseFetchMixin):
    """Scrape any real-estate site by having an AI analyze the DOM.

    The adapter first asks Qwen 3.6 Flash to map out the listing-page
    structure (card selectors, detail-link patterns, pagination). It then
    crawls detail pages and asks the AI to extract structured fields from
    each.
    """

    def __init__(self, source_id: Optional[int] = None,
                 crawl_config: dict | None = None,
                 api_key: str = "",
                 base_url: str = "",
                 model: str = ""):
        super().__init__(source_id)
        cfg = crawl_config or {}
        self.seed_url = cfg.get("seed_url", "")
        self.base_url = self._derive_base_url(self.seed_url)
        self.init_fetch(base_url=self.base_url, crawl_config=cfg)
        self.api_key = api_key
        
        # Load fallback defaults from global settings if not provided
        from core.config import settings
        self.ai_base_url = base_url or settings.qwen_base_url
        self.ai_model = model or settings.qwen_model
        
        self._client: Optional[OpenAI] = None
        self._structure_cache: dict[str, dict] = {}

    @staticmethod
    def _derive_base_url(seed_url: str) -> str:
        p = urlparse(seed_url)
        return f"{p.scheme}://{p.netloc}"

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.ai_base_url,
            )
        return self._client

    # ------------------------------------------------------------------ #
    # Phase 1: AI analyzes listing-page structure
    # ------------------------------------------------------------------ #
    def analyze_structure(self, html: str, page_url: str) -> dict:
        """Ask AI to discover card selectors, detail URLs, pagination."""
        domain = urlparse(page_url).netloc
        cache_key = hashlib.sha256(domain.encode()).hexdigest()[:12]
        if cache_key in self._structure_cache:
            return self._structure_cache[cache_key]

        soup = BeautifulSoup(html, "html.parser")
        cleaned = _clean_html(soup)
        result = _ai_call(self.client, SYSTEM_PROMPT_STRUCTURE, cleaned, model=self.ai_model)
        self._structure_cache[cache_key] = result
        return result

    # ------------------------------------------------------------------ #
    # Phase 2: extract listing URLs from index page using AI selectors
    # ------------------------------------------------------------------ #
    def extract_listing_urls(self, html: str, structure: dict) -> list[str]:
        """Use AI-discovered selectors to find detail-page URLs from cards."""
        soup = BeautifulSoup(html, "html.parser")
        card_sel = structure.get("card_selector", "")
        link_sel = structure.get("detail_link_selector", "")
        urls: list[str] = []
        seen: set[str] = set()

        cards = soup.select(card_sel) if card_sel else []
        if not cards:
            # Fallback: try to find article elements with property-like classes
            cards = soup.select("article[class*='property'], article[class*='listing'], div[class*='property-item'], div[class*='listing-card']")

        for card in cards:
            a_tag = None
            if link_sel:
                a_tag = card.select_one(link_sel)
            if not a_tag:
                a_tag = card.find("a", href=True)
            if not a_tag:
                continue
            href = a_tag.get("href", "")
            full = urljoin(self.base_url, href)
            # Skip non-detail URLs (nav, pagination, homepage)
            parsed = urlparse(full)
            if parsed.path in ("/", "") or parsed.path == urlparse(self.base_url).path:
                continue
            if full in seen:
                continue
            seen.add(full)
            urls.append(full)

        print(f"[ai_scraper] cards found: {len(cards)}, detail URLs extracted: {len(urls)}")
        return urls

    # ------------------------------------------------------------------ #
    # Phase 3: AI extracts fields from a detail page
    # ------------------------------------------------------------------ #
    def extract_detail(self, html: str, detail_url: str) -> Optional[RawListingDraft]:
        """Ask AI to extract property fields from a detail page."""
        soup = BeautifulSoup(html, "html.parser")
        cleaned = _clean_detail_html(soup)
        extracted = _ai_call(self.client, SYSTEM_PROMPT_EXTRACT, cleaned, model=self.ai_model)
        if not extracted or not extracted.get("title"):
            print(f"[ai_scraper] AI extraction empty for {detail_url[:80]}")
            return None

        title = extracted.get("title", "Untitled")
        price_parsed = extracted.get("price_parsed")
        # Sanity check price
        if price_parsed and (price_parsed < 0 or price_parsed > 9_000_000_000):
            price_parsed = None

        images = [u for u in (extracted.get("images") or []) if isinstance(u, str) and u.startswith("http")]
        prop_type = extracted.get("property_type") or self._classify_from_title(title)

        return RawListingDraft(
            url_source=detail_url,
            title_raw=title,
            price_raw=extracted.get("price_raw"),
            price_parsed=price_parsed,
            currency=extracted.get("currency", "XAF"),
            location_raw=extracted.get("location"),
            description_raw=extracted.get("description"),
            property_type_raw=prop_type,
            images_raw=images,
            bedrooms=extracted.get("bedrooms"),
            bathrooms=extracted.get("bathrooms"),
            area_sqm=extracted.get("area_sqm"),
            confidence=0.50,  # AI-extracted starts at medium confidence
            payload={
                "ai_extracted": True,
                "ai_model": self.ai_model,
                "extra_features": extracted.get("features", []),
                "listing_purpose": extracted.get("listing_purpose"),
            },
        )

    @staticmethod
    def _classify_from_title(title: str) -> str:
        t = title.lower()
        if any(w in t for w in ["studio"]):
            return "Studio"
        if any(w in t for w in ["duplex"]):
            return "Duplex"
        if any(w in t for w in ["triplex"]):
            return "Triplex"
        if any(w in t for w in ["villa"]):
            return "Villa"
        if any(w in t for w in ["maison", "résidence"]):
            return "Maison"
        if any(w in t for w in ["appartement", "appart", "f2", "f3", "f4", "f5"]):
            return "Appartement"
        if any(w in t for w in ["chambre", "chambres"]):
            return "Chambre"
        if any(w in t for w in ["terrain", "parcelle"]):
            return "Terrain"
        if any(w in t for w in ["immeuble", "immeubles"]):
            return "Immeuble"
        if any(w in t for w in ["bureau", "bureaux", "commerce", "commercial", "magasin", "boutique"]):
            return "Bureau"
        return "Appartement"

    # ------------------------------------------------------------------ #
    # Phase 4: pagination
    # ------------------------------------------------------------------ #
    def discover_next_pages(self, html: str, structure: dict) -> list[str]:
        """Use AI-discovered pagination to find next pages."""
        soup = BeautifulSoup(html, "html.parser")
        pages: list[str] = []
        pag_sel = structure.get("pagination_selector", "")
        next_text = structure.get("next_page_text", "").lower()

        if pag_sel:
            for a in soup.select(pag_sel):
                href = a.get("href", "")
                if not href:
                    continue
                full = urljoin(self.base_url, href)
                pages.append(full)

        if not pages and next_text:
            for a in soup.find_all("a", href=True):
                if next_text in a.get_text(" ", strip=True).lower():
                    pages.append(urljoin(self.base_url, a["href"]))

        return pages

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #
    def fetch_listings(self, max_pages: int | None = None,
                       max_listings: int | None = None, **kwargs) -> list[RawListingDraft]:
        """Crawl the site and return extracted drafts.

        ``max_pages`` caps how many listing/index pages we traverse.
        ``max_listings`` caps how many complete property drafts we return —
        once enough have been extracted, pagination and detail-page fetches
        stop. ``None`` means unlimited.
        """
        max_pages = max_pages or 5
        drafts: list[RawListingDraft] = []
        seen_detail_urls: set[str] = set()

        print(f"[ai_scraper] === Starting AI-powered scrape of {self.seed_url} ===")

        # Step 1: fetch seed page
        html = self.fetch_text(self.seed_url, referer=self.base_url)
        if not html:
            print("[ai_scraper] Failed to fetch seed page")
            return drafts

        # Step 2: AI analyzes structure
        print("[ai_scraper] Phase 1: AI analyzing page structure ...")
        structure = self.analyze_structure(html, self.seed_url)
        print(f"[ai_scraper] Structure: {json.dumps(structure, indent=2, ensure_ascii=False)[:500]}")

        # Step 3: collect listing URLs from seed + pagination
        all_detail_urls: list[str] = []
        pages_to_crawl = [self.seed_url]
        crawled_pages = 0

        while pages_to_crawl and crawled_pages < max_pages:
            page_url = pages_to_crawl.pop(0)
            if crawled_pages > 0:
                html = self.fetch_text(page_url, referer=self.base_url)
                if not html:
                    continue
                # Re-analyze structure if needed
                structure = self.analyze_structure(html, page_url)

            detail_urls = self.extract_listing_urls(html, structure)
            crawled_pages += 1

            new_urls = [u for u in detail_urls if u not in seen_detail_urls]
            all_detail_urls.extend(new_urls)
            seen_detail_urls.update(new_urls)

            # Pagination
            next_pages = self.discover_next_pages(html, structure)
            for np_url in next_pages:
                if np_url not in pages_to_crawl and np_url not in [self.seed_url]:
                    pages_to_crawl.append(np_url)

            print(f"[ai_scraper] Page {crawled_pages}: {len(detail_urls)} detail URLs, "
                  f"{len(next_pages)} next pages, {len(all_detail_urls)} total unique")

            # Stop paginating once we've collected enough detail URLs.
            if max_listings and len(all_detail_urls) >= max_listings:
                print(f"[ai_scraper] Reached max_listings={max_listings} URLs, stopping pagination")
                break

        print(f"[ai_scraper] Phase 2 done: {len(all_detail_urls)} detail URLs to scrape")

        # Step 4: extract details from each listing page
        # Slice to max_listings so we don't fetch detail pages we'll discard.
        urls_to_scrape = all_detail_urls[:max_listings] if max_listings else all_detail_urls
        for i, detail_url in enumerate(urls_to_scrape):
            print(f"[ai_scraper] Phase 3 [{i+1}/{len(urls_to_scrape)}]: {detail_url[:100]}")
            detail_html = self.fetch_text(detail_url, referer=self.base_url)
            if not detail_html:
                continue
            draft = self.extract_detail(detail_html, detail_url)
            if draft:
                drafts.append(draft)
                print(f"  -> {draft.title_raw[:70]} | {draft.price_parsed} {draft.currency} | {draft.property_type_raw}")
                if max_listings and len(drafts) >= max_listings:
                    print(f"[ai_scraper] Reached max_listings={max_listings} drafts, stopping")
                    break
            time.sleep(0.5)  # Be polite

        print(f"[ai_scraper] === Done: {len(drafts)} drafts extracted ===")
        return drafts

    # Required by SourceAdapter ABC
    def fetch_details(self, listing_url: str) -> Optional[RawListingDraft]:
        html = self.fetch_text(listing_url, referer=self.base_url)
        if not html:
            return None
        return self.extract_detail(html, listing_url)

    def normalize_data(self, raw: dict) -> RawListingDraft:
        return RawListingDraft(
            url_source=raw.get("url_source", ""),
            title_raw=raw.get("title_raw", "Untitled"),
            price_raw=raw.get("price_raw"),
            price_parsed=raw.get("price_parsed"),
            currency=raw.get("currency", "XAF"),
            location_raw=raw.get("location_raw"),
            description_raw=raw.get("description_raw"),
            property_type_raw=raw.get("property_type_raw", "Appartement"),
            images_raw=raw.get("images_raw", []),
            confidence=raw.get("confidence", 0.5),
            payload=raw.get("payload", {}),
        )

    def validate_data(self, draft: RawListingDraft) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not draft.title_raw or draft.title_raw == "Untitled":
            errors.append("missing_title")
        if not draft.url_source:
            errors.append("missing_url")
        return (len(errors) == 0, errors)
