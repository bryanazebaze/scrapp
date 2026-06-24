"""Natural-language search endpoint.

Parses queries like:
  "3-bedroom house in Bastos under 120M"
  "appartement à Douala Akwa entre 30 et 50 millions"
  "villa with pool in Yaoundé"

Two parsing strategies:
  1. AI-assisted: sends the query to Qwen (DashScope) which returns structured
     JSON filters. Used when DASHSCOPE_API_KEY is configured.
  2. Regex fallback: keyword/regex extraction. Always available.
"""
from __future__ import annotations

import re
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.ai_search import ai_parse_search_query
from core.database import get_db
from core.models import CanonicalProperty, Location, RawListing
from core.schemas import AnnonceBreve
from api.annonces import _canon_to_breve
from scrapers.utils import (
    CAMEROON_CITIES, CAMEROON_NEIGHBORHOODS, classify_property_type,
)

router = APIRouter(prefix="/search", tags=["search"])


# Common French/English grammatical stopwords to strip before keyword
# fallback search. Property-type words (appartement, villa, etc.) are
# intentionally NOT stopwords — they are meaningful search keywords.
_STOPWORDS = {
    "a", "à", "au", "aux", "avec", "de", "des", "du", "en", "et", "la",
    "le", "les", "un", "une", "pour", "dans", "sur", "by", "the",
    "in", "of", "and", "or", "with", "under", "over", "between", "is",
    "to", "at", "for", "on", "max", "min", "plus", "moins", "jusqu",
    "seulement", "million", "millions", "that", "this", "these", "those",
}


def _extract_keywords(q: str) -> list[str]:
    """Split a query into search keywords, dropping stopwords and short tokens."""
    tokens = re.split(r"\s+", q.lower().strip())
    keywords = []
    for t in tokens:
        t = t.strip(".,;:!?'\"()[]-")
        if len(t) >= 3 and t not in _STOPWORDS:
            keywords.append(t)
    return keywords


def _keyword_fallback_query(keywords: list[str], db: Session):
    """Build a query that matches any keyword in title or description."""
    query = db.query(CanonicalProperty).filter(
        CanonicalProperty.is_active == True,
        CanonicalProperty.current_best_price.isnot(None),
    )
    clauses = []
    for kw in keywords:
        clauses.append(CanonicalProperty.title_canonical.ilike(f"%{kw}%"))
        desc_exists = (
            db.query(RawListing.id)
            .filter(
                RawListing.canonical_property_id == CanonicalProperty.id,
                RawListing.description_raw.ilike(f"%{kw}%"),
            )
            .exists()
        )
        clauses.append(desc_exists)
    if clauses:
        query = query.filter(or_(*clauses))
    return query


# --------------------------------------------------------------------------- #
# Regex-based query parser (fallback)
# --------------------------------------------------------------------------- #
def parse_search_query(q: str) -> dict:
    """Parse a natural-language search string into filter criteria."""
    q_lower = q.lower().strip()
    filters: dict = {}

    # Bedrooms: "3 bedroom", "3-bedroom", "3 chambres", "3 pièces"
    m = re.search(r"(\d+)\s*[-_]?\s*(?:bedroom|bedrooms|chambre|chambres|pièces?|piece|pieces|ch)", q_lower)
    if m:
        filters["min_bedrooms"] = int(m.group(1))

    # Bathrooms: "2 bathroom", "2 salle de bain"
    m = re.search(r"(\d+)\s*(?:bathroom|bathrooms|salle[s]? de bain|bath)", q_lower)
    if m:
        filters["min_bathrooms"] = int(m.group(1))

    # Area: "100 sqm", "100m2", "100 m2", "100 mètres carrés"
    m = re.search(r"(\d+)\s*(?:sqm|m2|m²|mètres? carrés?|metres? carres?)", q_lower)
    if m:
        filters["min_area"] = float(m.group(1))

    # Price ceiling: "under 120M", "moins de 120 millions", "max 120M"
    m = re.search(r"(?:under|max|moins de|maximum|jusqu[']?à|<=?)\s*(\d+(?:\.\d+)?)\s*(m|million|millions|k|kilo|b|billion)?", q_lower)
    if m:
        val = float(m.group(1))
        unit = (m.group(2) or "")
        if unit.startswith("m"):
            val *= 1_000_000
        elif unit.startswith("k"):
            val *= 1_000
        elif unit.startswith("b"):
            val *= 1_000_000_000
        filters["max_price"] = int(val)

    # Price floor: "over 50M", "plus de 50 millions", "min 50M"
    m = re.search(r"(?:over|min|plus de|minimum|au moins|>=?)\s*(\d+(?:\.\d+)?)\s*(m|million|millions|k|kilo|b|billion)?", q_lower)
    if m:
        val = float(m.group(1))
        unit = (m.group(2) or "")
        if unit.startswith("m"):
            val *= 1_000_000
        elif unit.startswith("k"):
            val *= 1_000
        elif unit.startswith("b"):
            val *= 1_000_000_000
        filters["min_price"] = int(val)

    # Price range: "between 30 and 50 millions", "entre 30 et 50M"
    m = re.search(r"(?:between|entre)\s*(\d+(?:\.\d+)?)\s*(?:and|et|-)\s*(\d+(?:\.\d+)?)\s*(m|million|millions|k|b)?", q_lower)
    if m:
        lo = float(m.group(1))
        hi = float(m.group(2))
        unit = (m.group(3) or "")
        if unit.startswith("m"):
            lo *= 1_000_000; hi *= 1_000_000
        elif unit.startswith("k"):
            lo *= 1_000; hi *= 1_000
        elif unit.startswith("b"):
            lo *= 1_000_000_000; hi *= 1_000_000_000
        filters["min_price"] = int(lo)
        filters["max_price"] = int(hi)

    # Property type: house, villa, apartment, appartement, studio, land, terrain
    type_map = {
        "villa": "Villa", "house": "Villa", "maison": "Maison",
        "apartment": "Appartement", "appartement": "Appartement", "appart": "Appartement",
        "studio": "Studio",
        "land": "Terrain", "terrain": "Terrain",
        "commercial": "Commercial", "bureau": "Bureau", "office": "Bureau",
        "duplex": "Duplex", "chambre": "Chambre",
    }
    for kw, ptype in type_map.items():
        if re.search(rf"\b{kw}\b", q_lower):
            filters["property_type"] = ptype
            break

    # City: match Cameroon cities mentioned in the query (case-insensitive)
    q_norm = q_lower
    for city in CAMEROON_CITIES:
        if city.lower() in q_norm:
            filters["city"] = city
            break

    # Neighborhood: match known neighborhoods (case-insensitive)
    for nb in CAMEROON_NEIGHBORHOODS:
        if nb.lower() in q_norm:
            filters["neighborhood"] = nb
            break

    return filters


# --------------------------------------------------------------------------- #
# Build SQLAlchemy query from filters
# --------------------------------------------------------------------------- #
def _build_query(filters: dict, db: Session):
    """Build a SQLAlchemy query on CanonicalProperty from a filters dict."""
    query = db.query(CanonicalProperty).filter(
        CanonicalProperty.is_active == True,
        CanonicalProperty.current_best_price.isnot(None),
    )
    if "property_type" in filters:
        query = query.filter(
            CanonicalProperty.property_type == filters["property_type"])
    if "keywords" in filters and filters["keywords"]:
        query = query.filter(
            CanonicalProperty.title_canonical.ilike(f"%{filters['keywords']}%"))
    if "city" in filters or "neighborhood" in filters:
        query = query.join(Location,
                           CanonicalProperty.location_id == Location.id)
        if "city" in filters:
            # "Ville ou Quartier" — match against both city and neighborhood
            query = query.filter(
                Location.city.ilike(f"%{filters['city']}%")
                | Location.neighborhood.ilike(f"%{filters['city']}%")
            )
        if "neighborhood" in filters:
            query = query.filter(
                Location.neighborhood.ilike(f"%{filters['neighborhood']}%"))
    if "min_price" in filters:
        query = query.filter(
            CanonicalProperty.current_best_price >= filters["min_price"])
    if "max_price" in filters:
        query = query.filter(
            CanonicalProperty.current_best_price <= filters["max_price"])
    if "min_bedrooms" in filters:
        query = query.filter(
            CanonicalProperty.bedrooms >= filters["min_bedrooms"])
    if "min_area" in filters:
        query = query.filter(CanonicalProperty.area_sqm >= filters["min_area"])
    return query


def _execute(query, db: Session, skip: int, limit: int) -> list[AnnonceBreve]:
    """Execute query and build AnnonceBreve results."""
    canons = query.order_by(CanonicalProperty.last_seen_at.desc()) \
                  .offset(skip).limit(limit).all()
    results = []
    for c in canons:
        best = db.query(RawListing).filter(
            RawListing.canonical_property_id == c.id,
            RawListing.price_parsed == c.current_best_price,
        ).first()
        results.append(_canon_to_breve(c, c.location, best))
    return results


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@router.get("", response_model=List[AnnonceBreve])
async def search(
    q: str = Query(..., description="Natural-language search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    city: Optional[str] = None,
    neighborhood: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    property_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Natural-language property search.

    Tries AI parsing (Qwen) first, falls back to regex parsing.
    Explicit query params (city, min_price, etc.) override parsed values.

    Examples:
      "3-bedroom house in Bastos under 120M"
      "appartement à Douala entre 30 et 50 millions"
      "villa with pool in Yaoundé"
    """
    # 1. Try AI parsing first
    filters = await ai_parse_search_query(q)

    # 2. Fall back to regex if AI failed
    if filters is None:
        filters = parse_search_query(q)

    # 3. Merge explicit query params (they take priority)
    if property_type:
        filters["property_type"] = property_type
    if city:
        filters["city"] = city
    if neighborhood:
        filters["neighborhood"] = neighborhood
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price

    # 4. Build and execute query
    query = _build_query(filters, db)
    results = _execute(query, db, skip, limit)

    # 5. Fallback: if no structured-filter results and the raw query is
    #    non-empty, search title/description for each extracted keyword.
    if not results and q.strip():
        keywords = _extract_keywords(q)
        if keywords:
            fb_query = _keyword_fallback_query(keywords, db)
            return _execute(fb_query, db, skip, limit)

    return results


@router.get("/ai")
async def ai_search_preview(
    q: str = Query(..., description="Query to parse"),
):
    """Debug endpoint: shows what the AI (or regex fallback) extracts.

    Returns {"fallback": bool, "parsed": {...}} showing the filter dict
    that would be applied to the database query.
    """
    result = await ai_parse_search_query(q)
    if result is None:
        return {"fallback": True, "parsed": parse_search_query(q)}
    return {"fallback": False, "parsed": result}