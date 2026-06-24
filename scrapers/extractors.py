"""Field extractors for the universal fallback scraper.

Three ordered strategies; first wins per field (per the plan). Each returns a
dict of partial fields it could extract:

  extract_jsonld(soup)    -> highest confidence (schema.org Product/Offer etc.)
  extract_opengraph(soup) -> medium (og:title/og:image/og:description)
  extract_heuristic(soup) -> lowest (h1, price regex, city dictionary, imgs)

`extract_all(soup)` runs all three and merges — for each field the JSON-LD
value is preferred, then OpenGraph, then heuristic. It also reports which
strategy supplied each field so the confidence scorer can weight it.
"""
from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup

from .utils import parse_price, classify_property_type, is_real_image, detect_city


# schema.org types that indicate a property/listing.
_SCHEMA_TYPES = {
    "product", "residence", "apartment", "house", "place",
    "offer", "singlefamilyresidence", "apartmentcomplex", "lodgingbusiness",
    "rental", "realestateagent",
}


def _extract_jsonld_node(node: dict) -> dict:
    """Pull property-relevant fields from one JSON-LD node."""
    out: dict[str, Any] = {}
    if not isinstance(node, dict):
        return out
    node_type = (node.get("@type") or "")
    if isinstance(node_type, list):
        node_types = {t.lower() for t in node_type if isinstance(t, str)}
    elif isinstance(node_type, str):
        node_types = {node_type.lower()}
    else:
        node_types = set()

    if node.get("name"):
        out["title"] = str(node["name"])
    if node.get("description"):
        out["description"] = str(node["description"])
    offers = node.get("offers")
    if isinstance(offers, dict):
        if "price" in offers:
            out["price_raw"] = str(offers["price"])
            out["price_parsed"] = parse_price(str(offers["price"]),
                                             min_value=1000, reject_per_sqm=True)
        if "priceCurrency" in offers:
            out["currency"] = str(offers["priceCurrency"])
    elif isinstance(offers, list):
        for o in offers:
            if isinstance(o, dict) and o.get("price"):
                out["price_raw"] = str(o["price"])
                out["price_parsed"] = parse_price(str(o["price"]),
                                                 min_value=1000, reject_per_sqm=True)
                if o.get("priceCurrency"):
                    out["currency"] = str(o["priceCurrency"])
                break
    # Images: schema.org image can be a string or list.
    img = node.get("image")
    if isinstance(img, str):
        out["images"] = [img]
    elif isinstance(img, list):
        out["images"] = [i for i in img if isinstance(i, str)]
    # Address.
    addr = node.get("address")
    if isinstance(addr, dict):
        loc = ", ".join(filter(None, [
            addr.get("addressLocality"), addr.get("addressRegion"),
            addr.get("addressCountry"),
        ]))
        if loc:
            out["location"] = loc
    elif isinstance(addr, str) and addr:
        out["location"] = addr
    # Geo.
    geo = node.get("geo")
    if isinstance(geo, dict):
        try:
            out["lat"] = float(geo.get("latitude"))
            out["lng"] = float(geo.get("longitude"))
        except (TypeError, ValueError):
            pass
    return out


def extract_jsonld(soup: BeautifulSoup) -> dict:
    """Parse all JSON-LD blocks; return fields from the first node that looks
    like a property/listing. Returns {} if none found."""
    out: dict = {}
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            # @graph wraps a list of nodes.
            if "@graph" in node and isinstance(node["@graph"], list):
                for sub in node["@graph"]:
                    extracted = _extract_jsonld_node(sub)
                    if extracted:
                        return extracted
            extracted = _extract_jsonld_node(node)
            if extracted:
                return extracted
    return out


def extract_opengraph(soup: BeautifulSoup) -> dict:
    """Extract og:title / og:description / og:image / og:url."""
    out: dict = {}
    for prop in ("og:title", "og:description", "og:image", "og:url"):
        tag = soup.find("meta", {"property": prop})
        if tag and tag.get("content"):
            key = prop.split(":", 1)[1]
            out[key] = tag["content"].strip()
    # Twitter cards as a fallback for image.
    if "image" not in out:
        tw = soup.find("meta", {"name": "twitter:image"})
        if tw and tw.get("content"):
            out["image"] = tw["content"].strip()
    images: list[str] = []
    if "image" in out:
        images.append(out.pop("image"))
        out["images"] = images
    return out


# Currency-tagged price: a number with thousand separators adjacent to a
# CFA/XAF/FCFA marker. We prefer these because bare digit runs on real-estate
# pages are often phone numbers (Cameroon +237 ...) or IDs.
_PRICE_TAGGED_RE = re.compile(
    r"(?:(?:XAF|FCFA|CFA)\s*(\d{1,3}(?:[ .,]\d{3})+|\d{4,}))"
    r"|(?:\b(\d{1,3}(?:[ .,]\d{3})+|\d{4,})\s*(?:XAF|FCFA|CFA))",
    re.IGNORECASE,
)
# Plausible price magnitude (avoid phone numbers, IDs, tiny noise).
_MIN_PRICE = 1_000
_MAX_PRICE = 10_000_000_000  # 10 billion XAF — above any plausible RE price


def _scan_price(text: str) -> tuple[str, int] | None:
    """Find the first currency-tagged price in `text`. Returns (raw, parsed)
    or None. Skips values out of the plausible range (rejects phone numbers
    that happen to sit next to 'CFA'-like tokens) and text containing '+'
    (phone prefixes)."""
    if "+" in text:
        # A '+' strongly implies a phone number even if a price-like token
        # appears nearby; skip the whole element to be safe.
        return None
    for m in _PRICE_TAGGED_RE.finditer(text):
        raw = m.group(0)
        parsed = parse_price(raw)
        if parsed and _MIN_PRICE <= parsed <= _MAX_PRICE:
            return raw, parsed
    return None


def extract_heuristic(soup: BeautifulSoup, base_url: str = "") -> dict:
    """Last-resort DOM heuristics: h1 -> title, currency-tagged price scan,
    city dictionary scan, image filtering."""
    out: dict = {}
    h1 = soup.find("h1")
    if h1:
        out["title"] = h1.get_text(strip=True)
    # Price: scan short text elements for a currency-tagged number.
    for el in soup.find_all(["span", "div", "p", "strong", "b"]):
        text = el.get_text(" ", strip=True)
        if not text or len(text) > 80:
            continue
        found = _scan_price(text)
        if found:
            out["price_raw"], out["price_parsed"] = found
            break
    # Location: city dictionary scan over short text.
    for el in soup.find_all(["span", "p", "div"]):
        text = el.get_text(" ", strip=True)
        if not text or len(text) > 100:
            continue
        city = detect_city(text)
        if city:
            out["location"] = text
            break
    # Images: filter logos/icons/tracking pixels; keep real ones.
    images: list[str] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src or not is_real_image(src):
            continue
        if src.startswith("http"):
            images.append(src)
        elif src.startswith("/") and base_url:
            images.append(base_url.rstrip("/") + src)
    if images:
        out["images"] = images[:8]
    # Property type from title if present.
    if "title" in out:
        out["property_type"] = classify_property_type(out["title"])
    return out


def extract_all(soup: BeautifulSoup, base_url: str = "") -> dict:
    """Run all three strategies and merge. Returns a dict with a `_source`
    map showing which strategy supplied each field, for confidence scoring."""
    jl = extract_jsonld(soup)
    og = extract_opengraph(soup)
    heur = extract_heuristic(soup)

    merged: dict[str, Any] = {}
    source: dict[str, str] = {}
    for field, val in jl.items():
        merged[field] = val
        source[field] = "jsonld"
    for field, val in og.items():
        if field not in merged or not merged.get(field):
            merged[field] = val
            source[field] = "opengraph"
    for field, val in heur.items():
        if field not in merged or not merged.get(field):
            merged[field] = val
            source[field] = "heuristic"

    # Images merge (concatenate unique).
    all_images: list[str] = []
    seen: set[str] = set()
    for src in (jl.get("images") or []) + (og.get("images") or []) + (heur.get("images") or []):
        if isinstance(src, str) and src not in seen:
            all_images.append(src)
            seen.add(src)
    if all_images:
        merged["images"] = all_images
        if "images" in jl:
            source["images"] = "jsonld"
        elif "images" in og:
            source["images"] = "opengraph"
        else:
            source["images"] = "heuristic"

    merged["_source"] = source
    merged["_has_jsonld_product"] = bool(jl)
    merged["_has_opengraph"] = bool(og)
    return merged