"""AI-assisted search query parsing using Qwen API.

Sends a natural-language search query to Qwen with a system prompt that
explains the Cameroon real-estate context. Qwen returns structured JSON
with filter criteria (city, neighborhood, property_type, price range, etc).

Falls back to the regex-based parser in api/search.py:parse_search_query
on any error (network, API, JSON parse, missing API key).
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from core.config import settings

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# System prompt — instructs Qwen to extract structured filters from NL queries
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """Tu es un assistant qui analyse des requêtes de recherche immobilière au Cameroun.

Extrais les critères de recherche depuis la requête de l'utilisateur et retourne-les
au format JSON avec les champs suivants (tous optionnels, omettre si non mentionné):

- property_type: un parmi "Appartement", "Studio", "Villa", "Terrain", "Bureau",
  "Commercial", "Duplex", "Chambre", "Maison"
- city: nom de la ville au Cameroun (ex: "Douala", "Yaoundé", "Bafoussam", "Bamenda",
  "Garoua", "Maroua", "Buea", "Limbe", "Kribi", "Ebolowa", "Bertoua", "Ngaoundéré")
- neighborhood: nom du quartier (ex: "Bonamoussadi", "Bastos", "Akwa", "Kotto",
  "Bonapriso", "Mendong", "Odza", "Mvog-Mbi", "Deido", "Bonanjo")
- min_price: prix minimum en XAF (entier)
- max_price: prix maximum en XAF (entier)
- min_bedrooms: nombre minimum de chambres (entier)
- min_area: surface minimum en m² (nombre)
- keywords: mots-clés de recherche textuelle (chaîne, pour recherche sur le titre)

Règles:
- Les prix en "millions" ou "M" doivent être multipliés par 1 000 000.
- Les prix en "milliers" ou "k" doivent être multipliés par 1 000.
- Si l'utilisateur dit "moins de X", c'est max_price. "Plus de X", c'est min_price.
- "entre X et Y" donne min_price=X, max_price=Y.
- "meublé" ou "furnished" va dans keywords.
- "jardin", "parking", "piscine", "wifi" vont dans keywords.
- Si l'utilisateur mentionne un quartier connu, mets-le dans neighborhood et
  déduis la ville correspondante si possible (Douala: Akwa, Bonanjo, Bonapriso,
  Bonamoussadi, Deido, Kotto, Logpom, Makepe, Bonamoussadi; Yaoundé: Bastos,
  Mendong, Mvog-Mbi, Odza, Essos, Mvan, Briqueterie, Ngoa-Ekéllé).
- Réponds UNIQUEMENT avec le JSON, sans texte additionnel ni explication.

Exemples:
"appartement à Bonamoussadi" -> {"property_type":"Appartement","neighborhood":"Bonamoussadi","city":"Douala"}
"studio à Yaoundé moins de 100000" -> {"property_type":"Studio","city":"Yaoundé","max_price":100000}
"villa 3 chambres à Bastos entre 50 et 80M" -> {"property_type":"Villa","min_bedrooms":3,"neighborhood":"Bastos","city":"Yaoundé","min_price":50000000,"max_price":80000000}
"terrain à Douala 500m2" -> {"property_type":"Terrain","city":"Douala","min_area":500}
"maison meublée avec parking à Bonapriso" -> {"property_type":"Maison","neighborhood":"Bonapriso","city":"Douala","keywords":"meublé parking"}
"""


# --------------------------------------------------------------------------- #
# Client management
# --------------------------------------------------------------------------- #
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    """Lazy-init the AsyncOpenAI client. Returns None if no API key configured."""
    global _client
    if not settings.qwen_api_key:
        return None
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
            timeout=120.0,
            max_retries=3,
        )
    return _client


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
_ALLOWED_KEYS = {
    "property_type", "city", "neighborhood",
    "min_price", "max_price",
    "min_bedrooms", "min_area", "keywords",
}


async def ai_parse_search_query(q: str) -> dict | None:
    """Parse a natural-language query via Qwen.

    Returns a dict with any of the _ALLOWED_KEYS, or None on any failure
    (missing API key, network error, invalid JSON, etc.) — the caller
    should fall back to the regex-based parser in that case.
    """
    client = _get_client()
    if client is None:
        logger.debug("AI search skipped: no QWEN_API_KEY configured")
        return None
    try:
        resp = await client.chat.completions.create(
            model=settings.qwen_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
            ],
            temperature=0.1,
            max_tokens=300,
            extra_body={"enable_thinking": False},
        )
        content = resp.choices[0].message.content
        if not content:
            return None
        # Strip markdown code fences if present (Qwen sometimes wraps JSON)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(content)
        # Validate and filter to only allowed keys with non-None values
        return {k: v for k, v in result.items()
                if k in _ALLOWED_KEYS and v is not None}
    except Exception:
        # Catch every exception (network, timeout, JSONDecodeError, KeyError,
        # ValueError, etc.) so the regex fallback runs. Never log the raw
        # API response, request payload, or tool-call-shaped content — a
        # generic message keeps internals out of client-facing logs.
        logger.warning("AI search parse failed; falling back to regex parser")
        return None