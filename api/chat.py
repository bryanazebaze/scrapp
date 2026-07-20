"""AI chat agent endpoint with Qwen 3.6 Flash function-calling.

Exposes POST /chat — a conversational agent that can call backend tools
to query the database in real-time. The agent uses Qwen 3.6 Flash's
OpenAI-compatible tool-calling capability to decide which tools to invoke
based on the user's message, then synthesizes a natural-language reply
from the tool results.

Tools available to the agent:
  1. search_properties       — NL or structured property search
  2. get_property_detail     — full detail of one property
  3. get_city_safety_profile — city security/safety info
  4. get_neighborhood_analytics — market scores for a neighborhood
  5. get_city_neighborhoods  — all neighborhoods in a city with analytics
  6. get_trending_neighborhoods — trending areas by growth score
  7. get_price_analysis      — market position of a property
  8. get_locations           — list all cities/neighborhoods

The API key comes from settings.qwen_api_key (in .env), never exposed
to the frontend. The same /chat endpoint serves both the Flutter mobile
app and the web client.
"""
from __future__ import annotations

import json
import logging
from typing import List

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.models import (
    CanonicalProperty, CityProfile, Location, NeighborhoodAnalytics,
    NeighborhoodProfile, RawListing, Source, ListingHistory, ListingTranslation,
)
from core.schemas import AnnonceBreve, ChatMessage, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Accent-insensitive matching helpers (same logic as api/search.py)
# --------------------------------------------------------------------------- #
_ACCENT_FROM = "éèêëàâäîïôöùûüçÉÈÊËÀÂÄÎÏÔÖÙÛÜÇ"
_ACCENT_TO   = "eeeeaaaiioouuucEEEEAAAIIOOUUUC"


def _sql_normalize(column):
    """SQL expression: lower() + remove French accents for ilike matching."""
    return func.translate(func.lower(column), _ACCENT_FROM, _ACCENT_TO)


def _norm(s: str) -> str:
    """Python-side: lower + remove accents."""
    table = str.maketrans(_ACCENT_FROM, _ACCENT_TO)
    return s.lower().translate(table)

router = APIRouter(prefix="/chat", tags=["chat"])


# --------------------------------------------------------------------------- #
# System prompt (bilingual — built dynamically based on user's language)
# --------------------------------------------------------------------------- #
def _build_system_prompt(lang: str = "fr") -> str:
    """Build the system prompt in the requested language."""
    if lang == "en":
        return """You are CentralBot, the intelligent assistant of CentralImmo, Cameroon's real-estate intelligence platform.

You help users find properties, assess city and neighborhood safety, understand the market, and analyze prices.

You have tools to query the database in real-time:
- search_properties: search properties (city, neighborhood, type, price, bedrooms, area)
- get_property_detail: full details of a property by ID
- get_city_safety_profile: city security profile (rating, threats, safe zones)
- get_neighborhood_analytics: market scores for a neighborhood — accepts the neighborhood name directly (e.g. neighborhood="Nkoabang", city="Yaounde"), no slug needed
- get_city_neighborhoods: all neighborhoods in a city
- get_trending_neighborhoods: trending areas by growth score
- get_price_analysis: price analysis of a property vs the market
- get_locations: list available cities and neighborhoods

IMPORTANT: City and neighborhood names are accent-insensitive. You can write "Yaounde" or "Yaounde", "Douala", "Bastos" — the system recognizes accents automatically.

RULES:
1. Respond in English. Be very concise: maximum 2-3 sentences per response.
2. Do NOT use markdown (no **, no ##, no tables).
3. Do NOT use emojis.
4. When you find properties, do not describe them individually — just state the count found and summarize the price range. Properties will be displayed as visual cards with images.
5. For the safest city: call get_locations then get_city_safety_profile to compare.
6. Suggest ONE follow-up question at the end.
7. Prices are in XAF. 1 million = 1,000,000 XAF.
8. For get_neighborhood_analytics: pass the neighborhood name directly (neighborhood) and optionally the city (city). No need to look up the slug.
9. For price analysis: lands (Terrain) are compared by XAF/m2 (price_per_sqm); structures (Appartement, Maison, Villa, ...) are compared by total XAF price. The response's comparison_metric tells you which. Always mention the metric when summarizing an analysis.
10. PROPERTY SEARCH: If the user asks to find, list, show, or search for properties (e.g. "rooms in Bastos", "cheapest property", "houses for sale", "any room at odza"), ALWAYS call search_properties. NEVER answer with property info from memory — always search the database first.
11. MULTIPLE TOOLS: You can call multiple tools in a single response. If the question involves multiple aspects (e.g. properties + neighborhood safety, or properties + market analysis), call multiple tools at once to gather all needed information before answering.
"""
    return """Tu es CentralBot, l'assistant intelligent de CentralImmo, la plateforme d'intelligence immobiliere du Cameroun.

Tu aides les utilisateurs a trouver des biens, evaluer la securite des villes et quartiers, comprendre le marche, et analyser les prix.

Tu disposes d'outils pour interroger la base de donnees en temps reel:
- search_properties: rechercher des biens (ville, quartier, type, prix, chambres, surface)
- get_property_detail: detail complet d'un bien par ID
- get_city_safety_profile: profil de securite d'une ville (rating, menaces, zones sures)
- get_neighborhood_analytics: scores du marche d'un quartier — accepte le nom du quartier directement (ex: neighborhood="Nkoabang", city="Yaounde"), pas besoin de slug
- get_city_neighborhoods: tous les quartiers d'une ville
- get_trending_neighborhoods: quartiers tendance
- get_price_analysis: analyse du prix d'un bien vs le marche
- get_locations: lister les villes et quartiers disponibles

IMPORTANT: Les noms de villes et quartiers sont accent-insensibles. Tu peux ecrire "Yaounde" ou "Yaounde", "Douala", "Bastos" — le systeme reconnait les accents automatiquement.

REGLES:
1. Reponds en francais. Sois TRES concis: maximum 2-3 phrases par reponse.
2. N'utilise PAS de markdown (pas de **, pas de ##, pas de tableaux).
3. N'utilises PAS d'emojis.
4. Quand tu trouves des proprietes, ne les decris pas individuellement — dis juste le nombre trouve et resume les prix. Les proprietes seront affichees en cartes visuelles avec images.
5. Pour la ville la plus sure: appelle get_locations puis get_city_safety_profile pour comparer.
6. Propose UNE question de suivi a la fin.
7. Les prix sont en XAF. 1 million = 1 000 000 XAF.
8. Pour get_neighborhood_analytics: passe directement le nom du quartier (neighborhood) et optionnellement la ville (city). Pas besoin de chercher le slug.
9. Pour l'analyse de prix: les terrains (Terrain) sont compares en XAF/m2 (price_per_sqm); les structures (Appartement, Maison, Villa, ...) sont compares sur le prix total en XAF. Le champ comparison_metric de la reponse indique lequel. Mentionne toujours cette unite quand tu resumes une analyse.
10. RECHERCHE DE BIENS: Si l'utilisateur demande de trouver, lister, voir ou chercher des biens (ex: "chambres a Bastos", "propriete la moins chere", "maisons a vendre", "chambre a odza"), appelle TOUJOURS search_properties. Ne reponds JAMAIS avec des infos sur des biens de memoire — cherche toujours dans la base de donnees.
11. OUTILS MULTIPLES: Tu peux appeler plusieurs outils dans une seule reponse. Si la question implique plusieurs aspects (ex: biens + securite du quartier, ou biens + analyse de marche), appelle plusieurs outils en meme temps pour collecter toutes les informations avant de repondre.
"""


# --------------------------------------------------------------------------- #
# Tool definitions (OpenAI function-calling format)
# --------------------------------------------------------------------------- #
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_properties",
            "description": "Rechercher des biens immobiliers au Cameroun. Supporte la recherche en langage naturel ou avec des filtres structures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Requete en langage naturel (ex: 'villa a Bastos moins de 100M')",
                    },
                    "city": {
                        "type": "string",
                        "description": "Ville (ex: Douala, Yaounde, Bafoussam)",
                    },
                    "neighborhood": {"type": "string", "description": "Quartier"},
                    "property_type": {
                        "type": "string",
                        "description": "Type de bien: Appartement, Studio, Villa, Terrain, Bureau, Maison, Duplex, Chambre",
                    },
                    "min_price": {"type": "integer", "description": "Prix minimum en XAF"},
                    "max_price": {"type": "integer", "description": "Prix maximum en XAF"},
                    "min_bedrooms": {"type": "integer", "description": "Nombre minimum de chambres"},
                    "min_area": {"type": "number", "description": "Surface minimum en m2"},
                    "limit": {"type": "integer", "description": "Nombre max de resultats (defaut 20)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_property_detail",
            "description": "Obtenir le detail complet d'une propriete par son ID (description, sources, historique des prix).",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {"type": "integer", "description": "ID de la propriete"},
                },
                "required": ["property_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_safety_profile",
            "description": "Obtenir le profil de securite d'une ville au Cameroun (rating de securite, menaces actuelles, zones les plus sures, contacts d'urgence, infos de couvre-feu).",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Nom de la ville (ex: Douala, Yaounde)"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_neighborhood_analytics",
            "description": "Obtenir les analytics du marche immobilier d'un quartier (prix median, scores de croissance, demande, activite, luxe). Vous pouvez utiliser le slug, ou le nom du quartier (avec optionnellement la ville). Accepte optionnellement un property_type pour des analytics par type de bien (Appartement, Maison, Terrain, ...).",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "Slug du quartier (ex: bonamoussadi-douala). Optionnel.",
                    },
                    "neighborhood": {
                        "type": "string",
                        "description": "Nom du quartier (ex: Bonamoussadi, Nkoabang, Odza). Accent-insensible.",
                    },
                    "city": {
                        "type": "string",
                        "description": "Ville du quartier (ex: Douala, Yaounde). Accent-insensible.",
                    },
                    "property_type": {
                        "type": "string",
                        "description": "Type de bien (Appartement, Maison, Terrain, Villa, ...). Si fourni, retourne les analytics pour ce type avec fallback ville si < 3 biens dans le quartier.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_neighborhoods",
            "description": "Lister tous les quartiers d'une ville avec leurs analytics (prix median, scores, tendances). Accepte optionnellement un property_type pour filtrer par type de bien.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Nom de la ville"},
                    "property_type": {
                        "type": "string",
                        "description": "Type de bien (Appartement, Maison, Terrain, ...). Si omis, retourne les analytics tous types confondus.",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_neighborhoods",
            "description": "Obtenir les quartiers les plus tendance (croissance des prix la plus eleveee).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Nombre de resultats (defaut 10)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_analysis",
            "description": "Analyser la position d'un bien sur le marche (comparaison avec des biens similaires dans la meme ville).",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {"type": "integer", "description": "ID de la propriete a analyser"},
                },
                "required": ["property_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_locations",
            "description": "Lister les villes et quartiers disponibles dans la base de donnees.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Filtrer par ville (optionnel). Sans ce parametre, retourne toutes les localisations.",
                    },
                },
            },
        },
    },
]


# --------------------------------------------------------------------------- #
# Qwen client management
# --------------------------------------------------------------------------- #
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    """Lazy-init the AsyncOpenAI client. Returns None if no API key."""
    global _client
    if not settings.qwen_api_key:
        return None
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
            timeout=120.0,  # 120s total — generous for unstable connections
            max_retries=3,  # SDK-level retries on transient failures
        )
    return _client


# --------------------------------------------------------------------------- #
# Tool execution functions
# --------------------------------------------------------------------------- #
def _track_listing_images(best_raw: RawListing | None) -> list[str]:
    """Extract non-tracking image URLs from a raw listing."""
    _TRACKING_HOSTS = (
        "facebook.com/tr", "facebook.net", "googletagmanager.com",
        "google-analytics.com", "doubleclick.net", "hotjar.com",
        "clarity.ms", "scorecardresearch", "quantserve.com",
    )
    if not best_raw or not best_raw.images_raw:
        return []
    return [
        u for u in best_raw.images_raw
        if isinstance(u, str) and not any(h in u.lower() for h in _TRACKING_HOSTS)
    ][:8]


def _canon_to_breve(c: CanonicalProperty, loc: Location | None,
                    best_raw: RawListing | None) -> AnnonceBreve:
    return AnnonceBreve(
        id=c.id,
        title=c.title_canonical,
        property_type=c.property_type,
        price=c.current_best_price,
        currency="XAF",
        city=loc.city if loc else None,
        neighborhood=loc.neighborhood if loc else None,
        location_slug=loc.slug if loc else None,
        lat=loc.lat if loc else None,
        lng=loc.lng if loc else None,
        bedrooms=c.bedrooms,
        bathrooms=c.bathrooms,
        area_sqm=c.area_sqm,
        images=_track_listing_images(best_raw),
        best_source=best_raw.source.slug if best_raw and best_raw.source else None,
    )


def _tool_search_properties(args: dict, db: Session, lang: str = "fr") -> dict:
    """Search properties using structured filters or NL query."""
    from api.search import _build_query, _execute, parse_search_query

    limit = min(args.get("limit", 20), 20)
    filters: dict = {}

    # If a NL query is provided, parse it with the regex parser
    query = args.get("query")
    if query:
        filters.update(parse_search_query(query))

    # Explicit params override parsed values
    for key in ("city", "neighborhood", "property_type"):
        if args.get(key):
            filters[key] = args[key]
    for key in ("min_price", "max_price", "min_bedrooms"):
        if args.get(key) is not None:
            filters[key] = args[key]
    if args.get("min_area") is not None:
        filters["min_area"] = args["min_area"]

    query_obj = _build_query(filters, db)
    results = _execute(query_obj, db, skip=0, limit=limit)
    return {
        "count": len(results),
        "properties": [r.model_dump() for r in results],
    }


def _tool_get_property_detail(args: dict, db: Session, lang: str = "fr") -> dict:
    """Get full detail of a property by ID."""
    property_id = args["property_id"]
    canon = db.query(CanonicalProperty).filter(
        CanonicalProperty.id == property_id
    ).first()
    if not canon:
        return {"error": f"Propriete #{property_id} non trouvee"}

    raws = db.query(RawListing).filter(
        RawListing.canonical_property_id == canon.id
    ).all()
    raws.sort(key=lambda r: r.price_parsed or float('inf'))

    best_raw = raws[0] if raws else None
    images = _track_listing_images(best_raw)

    history = db.query(ListingHistory).filter(
        ListingHistory.canonical_property_id == canon.id
    ).order_by(ListingHistory.observed_at.asc()).all()

    sources = []
    for r in raws:
        src = db.query(Source).filter(Source.id == r.source_id).first()
        sources.append({
            "source": src.display_name if src else None,
            "url": r.url_source,
            "price": r.price_parsed,
        })

    # Use English translation if available and user is in EN mode
    description = best_raw.description_raw if best_raw else None
    if lang == "en" and best_raw:
        translation = db.query(ListingTranslation).filter(
            ListingTranslation.raw_listing_id == best_raw.id,
            ListingTranslation.language == "en",
        ).first()
        if translation:
            description = translation.description

    return {
        "id": canon.id,
        "title": canon.title_canonical,
        "property_type": canon.property_type,
        "price": canon.current_best_price,
        "city": canon.location.city if canon.location else None,
        "neighborhood": canon.location.neighborhood if canon.location else None,
        "bedrooms": canon.bedrooms,
        "bathrooms": canon.bathrooms,
        "area_sqm": canon.area_sqm,
        "description": description,
        "images": images,
        "sources": sources,
        "price_history": [
            {"event": h.event_type, "price": h.price_observed,
             "date": h.observed_at.isoformat() if h.observed_at else None}
            for h in history
        ],
    }


def _tool_get_city_safety_profile(args: dict, db: Session, lang: str = "fr") -> dict:
    """Get city security profile."""
    from api.profiles import localize_city
    city = args["city"]
    norm_city = _norm(city)
    profile = db.query(CityProfile).filter(
        _sql_normalize(CityProfile.city) == norm_city
    ).first()
    if not profile:
        return {"error": f"Pas de profil de securite pour la ville '{city}'"}
    return localize_city(profile, lang)


def _tool_get_neighborhood_analytics(args: dict, db: Session, lang: str = "fr") -> dict:
    """Get market analytics for a neighborhood by slug or name.

    Accepts an optional `property_type` to return per-type analytics with a
    geographic fallback to the city-level aggregate when the neighborhood has
    fewer than 3 listings of that type.
    """
    from core.analytics import find_location_by_slug, get_location_analytics
    slug = args.get("slug")
    neighborhood = args.get("neighborhood")
    city = args.get("city")
    property_type = args.get("property_type")

    loc = None
    # Try slug first
    if slug:
        loc = find_location_by_slug(db, slug)
    # Fallback: look up by neighborhood name (accent-insensitive)
    if not loc and neighborhood:
        norm_nb = _norm(neighborhood)
        q = db.query(Location).filter(
            _sql_normalize(Location.neighborhood) == norm_nb
        )
        if city:
            norm_city = _norm(city)
            q = q.filter(_sql_normalize(Location.city) == norm_city)
        loc = q.first()
    if not loc:
        ref = slug or neighborhood or city or "?"
        return {"error": f"Localisation '{ref}' non trouvee. Utilisez get_locations pour lister les quartiers disponibles."}
    analytics = get_location_analytics(db, loc.id, property_type=property_type)
    if not analytics:
        return {"error": f"Pas d'analytics pour '{slug}' encore. Executez 'python cli.py analytics'."}
    return {
        "location_id": loc.id,
        "city": loc.city,
        "neighborhood": loc.neighborhood,
        "slug": loc.slug,
        "property_type": analytics.property_type,
        "category": analytics.category,
        "listing_count": analytics.listing_count,
        "average_price": analytics.average_price,
        "median_price": analytics.median_price,
        "min_price": analytics.min_price,
        "max_price": analytics.max_price,
        "price_per_sqm": analytics.price_per_sqm,
        "min_price_per_sqm": analytics.min_price_per_sqm,
        "max_price_per_sqm": analytics.max_price_per_sqm,
        "avg_price_per_sqm": analytics.avg_price_per_sqm,
        "fallback_level": getattr(analytics, "fallback_level", None),
        "premium_score": analytics.premium_score,
        "demand_score": analytics.demand_score,
        "growth_score": analytics.growth_score,
        "activity_score": analytics.activity_score,
        "luxury_score": analytics.luxury_score,
        "trend_direction": analytics.trend_direction,
        "trend_pct": analytics.trend_pct,
    }


def _tool_get_city_neighborhoods(args: dict, db: Session, lang: str = "fr") -> dict:
    """Get all neighborhoods in a city with their analytics.

    When `property_type` is provided, returns per-type rows for that type
    (with city-level fallback for neighborhoods with < 3 listings of that
    type). Otherwise returns the all-types pooled row per neighborhood.
    """
    from core.analytics import get_location_analytics
    city = args["city"]
    property_type = args.get("property_type")
    norm_city = _norm(city)
    locs = db.query(Location).filter(
        _sql_normalize(Location.city) == norm_city
    ).all()
    if not locs:
        return {"error": f"Aucune localisation trouvee pour la ville '{city}'"}
    results = []
    for loc in locs:
        a = get_location_analytics(db, loc.id, property_type=property_type)
        if a:
            results.append({
                "slug": loc.slug,
                "neighborhood": loc.neighborhood,
                "property_type": a.property_type,
                "category": a.category,
                "listing_count": a.listing_count,
                "average_price": a.average_price,
                "median_price": a.median_price,
                "min_price": a.min_price,
                "max_price": a.max_price,
                "price_per_sqm": a.price_per_sqm,
                "min_price_per_sqm": a.min_price_per_sqm,
                "max_price_per_sqm": a.max_price_per_sqm,
                "avg_price_per_sqm": a.avg_price_per_sqm,
                "fallback_level": getattr(a, "fallback_level", None),
                "growth_score": a.growth_score,
                "demand_score": a.demand_score,
                "activity_score": a.activity_score,
                "trend_direction": a.trend_direction,
                "trend_pct": a.trend_pct,
            })
    return {"city": city, "neighborhoods": results}


def _tool_get_trending_neighborhoods(args: dict, db: Session, lang: str = "fr") -> dict:
    """Get trending neighborhoods by growth score."""
    limit = min(args.get("limit", 10), 50)
    rows = db.query(NeighborhoodAnalytics).filter(
        NeighborhoodAnalytics.property_type.is_(None),
        NeighborhoodAnalytics.growth_score.isnot(None),
    ).order_by(NeighborhoodAnalytics.growth_score.desc()).limit(limit).all()
    results = []
    for a in rows:
        loc = db.query(Location).filter(Location.id == a.location_id).first()
        if loc:
            results.append({
                "slug": loc.slug,
                "city": loc.city,
                "neighborhood": loc.neighborhood,
                "growth_score": a.growth_score,
                "trend_pct": a.trend_pct,
                "median_price": a.median_price,
            })
    return {"trending": results}


def _tool_get_price_analysis(args: dict, db: Session, lang: str = "fr") -> dict:
    """Category-aware price analysis for a property.

    Uses core.analytics.compute_price_analysis: structures (Appartement,
    Maison, ...) are compared by total price; lands (Terrain) are compared
    by XAF/m2. Falls back to city-wide comparables when the neighborhood has
    fewer than 3 same-type comparables.
    """
    from core.analytics import compute_price_analysis
    property_id = args["property_id"]
    canon = db.query(CanonicalProperty).filter(
        CanonicalProperty.id == property_id
    ).first()
    if not canon:
        return {"error": f"Propriete #{property_id} non trouvee"}
    return compute_price_analysis(db, canon)


def _tool_get_locations(args: dict, db: Session, lang: str = "fr") -> dict:
    """List all cities and neighborhoods."""
    q = db.query(Location)
    if args.get("city"):
        norm_city = _norm(args["city"])
        q = q.filter(_sql_normalize(Location.city) == norm_city)
    locs = q.order_by(Location.city, Location.neighborhood).all()
    # Group by city for a cleaner summary
    cities: dict[str, list[str]] = {}
    for loc in locs:
        cities.setdefault(loc.city, []).append(loc.neighborhood or loc.city)
    return {
        "cities": [
            {"city": city, "neighborhoods": nbs}
            for city, nbs in cities.items()
        ],
        "total_locations": len(locs),
    }


# Tool dispatch table
TOOL_FUNCTIONS = {
    "search_properties": _tool_search_properties,
    "get_property_detail": _tool_get_property_detail,
    "get_city_safety_profile": _tool_get_city_safety_profile,
    "get_neighborhood_analytics": _tool_get_neighborhood_analytics,
    "get_city_neighborhoods": _tool_get_city_neighborhoods,
    "get_trending_neighborhoods": _tool_get_trending_neighborhoods,
    "get_price_analysis": _tool_get_price_analysis,
    "get_locations": _tool_get_locations,
}


def _execute_tool(name: str, args: dict, db: Session, lang: str = "fr") -> dict:
    """Execute a tool by name. Returns a dict result."""
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Outil inconnu: {name}"}
    try:
        return fn(args, db, lang)
    except Exception as e:
        logger.exception("Tool %s failed", name)
        return {"error": f"Erreur lors de l'execution de l'outil: {e}"}


# --------------------------------------------------------------------------- #
# Property extraction from tool results
# --------------------------------------------------------------------------- #
def _extract_properties(tool_results: list[dict]) -> list[AnnonceBreve]:
    """Extract AnnonceBreve objects from tool call results."""
    properties: list[AnnonceBreve] = []
    for result in tool_results:
        if not isinstance(result, dict):
            continue
        # search_properties returns {"properties": [...]}
        raw_props = result.get("properties", [])
        for p in raw_props:
            try:
                properties.append(AnnonceBreve.model_validate(p))
            except Exception:
                pass
    return properties


# --------------------------------------------------------------------------- #
# Chat endpoint
# --------------------------------------------------------------------------- #
MAX_TOOL_ROUNDS = 3


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Conversational AI agent with tool-calling.

    Sends the user message to Qwen 3.6 Flash with tool definitions. If Qwen
    requests tool calls, executes them against the database, then sends
    results back to Qwen for a final natural-language reply.
    """
    client = _get_client()
    lang = req.language if req.language in ("fr", "en") else "fr"
    if client is None:
        no_key_msg = (
            "Je suis desole, le service d'assistant IA n'est pas configure. "
            "Contactez l'administrateur pour activer la cle API."
            if lang == "fr"
            else "I'm sorry, the AI assistant service is not configured. "
                 "Contact the administrator to activate the API key."
        )
        return ChatResponse(
            reply=no_key_msg,
            properties=[],
        )

    # Build the messages array with language-appropriate system prompt
    system_prompt = _build_system_prompt(lang)
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in req.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.message})

    tool_results: list[dict] = []
    tool_used_names: list[str] = []
    tool_metadata: dict | None = None

    # Tools whose results should be passed as structured metadata for UI cards
    _METADATA_TOOLS = {
        "get_city_safety_profile": "safety",
        "get_neighborhood_analytics": "analytics",
        "get_city_neighborhoods": "neighborhoods",
        "get_trending_neighborhoods": "trending",
        "get_price_analysis": "price_analysis",
        "get_locations": "locations",
    }

    for _round in range(MAX_TOOL_ROUNDS):
        try:
            kwargs: dict = dict(
                model=settings.qwen_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1500,
                extra_body={"enable_thinking": False},
            )
            resp = await client.chat.completions.create(**kwargs)
        except Exception as e:
            logger.exception("Qwen API call failed")
            error_msg = (
                "Je rencontre une difficulte technique. Pouvez-vous reformuler votre question ?"
                if lang == "fr"
                else "I'm experiencing a technical issue. Could you rephrase your question?"
            )
            return ChatResponse(
                reply=error_msg,
                properties=[],
                tool_metadata=tool_metadata,
            )

        choice = resp.choices[0]
        msg = choice.message

        # If no tool calls, we have the final answer
        if not msg.tool_calls:
            return ChatResponse(
                reply=msg.content or "Je n'ai pas de reponse pour le moment.",
                properties=_extract_properties(tool_results),
                tool_used=", ".join(tool_used_names) if tool_used_names else None,
                tool_metadata=tool_metadata,
            )

        # Append the assistant message with tool calls to the conversation
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        # Execute each tool call
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            tool_name = tc.function.name
            if tool_name not in tool_used_names:
                tool_used_names.append(tool_name)

            result = _execute_tool(tool_name, args, db, lang)
            tool_results.append(result)

            # Collect metadata for UI card rendering (last non-search tool wins)
            if tool_name in _METADATA_TOOLS and "error" not in result:
                tool_metadata = {
                    "type": _METADATA_TOOLS[tool_name],
                    "data": result,
                }

            # Append tool result to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str, ensure_ascii=False),
            })

    # If we exhausted tool-call rounds, get a final text response
    try:
        kwargs: dict = dict(
            model=settings.qwen_model,
            messages=messages,
            temperature=0.3,
            max_tokens=800,
            extra_body={"enable_thinking": False},
        )
        resp = await client.chat.completions.create(**kwargs)
        fallback_msg = (
            "Je n'ai pas pu traiter votre demande."
            if lang == "fr"
            else "I couldn't process your request."
        )
        reply = resp.choices[0].message.content or fallback_msg
    except Exception:
        reply = (
            "Je n'ai pas pu traiter votre demande completement."
            if lang == "fr"
            else "I couldn't fully process your request."
        )

    return ChatResponse(
        reply=reply,
        properties=_extract_properties(tool_results),
        tool_used=", ".join(tool_used_names) if tool_used_names else None,
        tool_metadata=tool_metadata,
    )