"""Confidence scoring for the universal scraper.

confidence = 0.40*f_schema + 0.20*f_struct + 0.15*f_price
           + 0.10*f_images + 0.10*f_location + 0.05*f_source

  f_schema   : 1.0 if JSON-LD Product/Offer found, 0.5 OpenGraph only, 0 heuristic only
  f_struct   : 1 if the detail URL was reached via a detected card container, else 0
  f_price    : 1 if price_parsed > 0
  f_images   : 1 if >=1 image URL resolves (HEAD 200) — passed in by the adapter
  f_location : 1 known city, 0.5 neighborhood, 0 otherwise
  f_source   : 1 if domain in the Cameroon real-estate allowlist

Thresholds (ingest gating, core.ingest._review_status_for):
  >= 0.75 : auto_promoted   (linked to/creates a canonical property)
  0.40-0.74: pending        (human review queue; canonical_property_id NULL)
  < 0.40  : rejected        (not stored as a raw_listing)

The factors are deliberately a 0/1 (or 0/0.5/1) set so the score is
explainable: the admin review UI can show exactly which signals fired.
"""
from __future__ import annotations

from .utils import detect_city, detect_neighborhood


# Domains we trust as Cameroon real-estate sources (seeded; extensible).
CAMEROON_RE_DOMAINS = {
    "mapiole.com", "kasastay.com", "weetyu.com", "lmplatinum.com",
    "estates.cm", "keurimmo.com", "agacam.com", "immobilier.cm",
}


def f_schema_value(extracted: dict) -> float:
    if extracted.get("_has_jsonld_product"):
        return 1.0
    if extracted.get("_has_opengraph"):
        return 0.5
    return 0.0


def f_location_value(location_raw: str | None) -> float:
    if not location_raw:
        return 0.0
    if detect_city(location_raw):
        return 1.0
    if detect_neighborhood(location_raw, None):
        return 0.5
    return 0.0


def f_source_value(url_source: str | None) -> float:
    if not url_source:
        return 0.0
    from urllib.parse import urlparse
    host = (urlparse(url_source).hostname or "").lower()
    host = host.removeprefix("www.")
    return 1.0 if host in CAMEROON_RE_DOMAINS else 0.0


def compute_confidence(extracted: dict, *, from_card: bool,
                       images_resolvable: bool, url_source: str | None) -> float:
    """Compute the 0..1 confidence score from the extraction result."""
    fs = f_schema_value(extracted)
    fstruct = 1.0 if from_card else 0.0
    fprice = 1.0 if (extracted.get("price_parsed") or 0) > 0 else 0.0
    fimages = 1.0 if images_resolvable else 0.0
    floc = f_location_value(extracted.get("location"))
    fsrc = f_source_value(url_source)
    return (
        0.40 * fs
        + 0.20 * fstruct
        + 0.15 * fprice
        + 0.10 * fimages
        + 0.10 * floc
        + 0.05 * fsrc
    )


def confidence_factors(extracted: dict, *, from_card: bool,
                       images_resolvable: bool, url_source: str | None) -> dict:
    """Return the individual factor values for explanation/debug."""
    return {
        "f_schema": f_schema_value(extracted),
        "f_struct": 1.0 if from_card else 0.0,
        "f_price": 1.0 if (extracted.get("price_parsed") or 0) > 0 else 0.0,
        "f_images": 1.0 if images_resolvable else 0.0,
        "f_location": f_location_value(extracted.get("location")),
        "f_source": f_source_value(url_source),
    }