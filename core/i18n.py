"""Internationalization helpers for the API layer.

Parses the Accept-Language header and provides mappings for the short
security_rating enum between French (the stored DB form) and English.
"""
from __future__ import annotations

from fastapi import Request

SUPPORTED_LANGS = ("fr", "en")
DEFAULT_LANG = "fr"

# security_rating is a short enum-like value stored in French in the DB.
# Map it to English in code rather than adding a column.
RATING_FR_TO_EN = {
    "Risque élevé": "High Risk",
    "Risque modéré": "Moderate Risk",
    "Risque faible": "Low Risk",
}
RATING_EN_TO_FR = {v: k for k, v in RATING_FR_TO_EN.items()}


def preferred_lang(request: Request) -> str:
    """Return 'en' or 'fr' based on the Accept-Language header.

    Default 'fr' (Cameroon's primary official language and the stored form).
    Looks at the first-listed language tag; falls back to 'fr' for anything
    that isn't English.
    """
    header = (request.headers.get("accept-language") or "").lower().strip()
    if not header:
        return DEFAULT_LANG
    first = header.split(",")[0].strip().split(";")[0].strip()
    return "en" if first.startswith("en") else DEFAULT_LANG


def rating_for_lang(value: str | None, lang: str) -> str | None:
    """Translate a security_rating value to the requested language."""
    if value is None:
        return None
    if lang == "en":
        return RATING_FR_TO_EN.get(value, value)
    return value


def pick(en_value, fr_value):
    """Return the English value when lang is 'en' and it is non-null,
    otherwise fall back to the French (stored) value.
    """
    if en_value is not None:
        return en_value
    return fr_value