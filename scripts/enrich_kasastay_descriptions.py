"""Enrich short Kasastay descriptions using structured data from location_raw.

The Kasastay cleaner fell back to title_raw for 27 listings where the scraper
captured no real description between the boilerplate. This script generates
better descriptions for those, plus for listings with very short cleaned text
(like "Deux douches\nOdza borne 10"), using:
  - title_raw (property name/number)
  - location_raw (contains "neighborhood, city · XAF price · type à neighborhood, N chambres")
  - price_parsed
  - property_type_raw
  - payload->bedrooms/bathrooms/area_sqm
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.database import SessionLocal
from core.models import RawListing, Source


def _parse_location_raw(loc_raw: str) -> dict:
    """Extract neighborhood, city, price, bedrooms from location_raw string.

    Format: "Yassa, Douala · XAF 120,000 · Appartement à Yassa, Douala, 2 chambres"
    """
    info = {}
    if not loc_raw:
        return info

    # Split on ·
    parts = [p.strip() for p in loc_raw.split("·")]
    for part in parts:
        # "Yassa, Douala" → neighborhood, city
        if "," in part and "XAF" not in part and "FCFA" not in part and "chambre" not in part.lower():
            sub = [s.strip() for s in part.split(",")]
            if len(sub) >= 2:
                info.setdefault("neighborhood", sub[0])
                info.setdefault("city", sub[1])
        # "XAF 120,000" → price
        m = re.search(r"(?:XAF|FCFA)\s*([\d\s,.]+)", part)
        if m:
            digits = re.sub(r"[^\d]", "", m.group(1))
            if digits:
                try:
                    info["price"] = int(digits)
                except ValueError:
                    pass
        # "Appartement à Yassa, Douala, 2 chambres" → bedrooms
        m = re.search(r"(\d+)\s*chambre", part, re.IGNORECASE)
        if m:
            info["bedrooms"] = int(m.group(1))
        # Property type
        m = re.search(r"(Appartement|Studio|Chambre|Duplex|Maison|Villa|Terrain|Bureau|Studio)\s*à", part, re.IGNORECASE)
        if m:
            info.setdefault("prop_type", m.group(1))

    return info


def _format_price(price: int | None) -> str:
    if not price or price <= 0:
        return ""
    return f"{price:,}".replace(",", " ")


def generate_description(listing: RawListing, loc_info: dict) -> str:
    """Generate a natural French description from available data."""
    title = listing.title_raw or ""
    prop_type = listing.property_type_raw or loc_info.get("prop_type") or "Bien immobilier"
    neighborhood = loc_info.get("neighborhood", "")
    city = loc_info.get("city", "")
    price = loc_info.get("price") or (listing.price_parsed if listing.price_parsed and listing.price_parsed > 0 else None)
    bedrooms = loc_info.get("bedrooms")
    baths = listing.payload.get("bathrooms") if listing.payload else None
    area = listing.payload.get("area_sqm") if listing.payload else None

    # Parse title for extra clues
    title_lower = title.lower()
    is_furnished = "meublé" in title_lower or "meuble" in title_lower
    is_titled = "titré" in title_lower or "titre" in title_lower

    # Build location string
    loc_str = neighborhood
    if city and city != neighborhood:
        loc_str = f"{neighborhood} à {city}" if neighborhood else city
    elif not loc_str and city:
        loc_str = city
    elif not loc_str:
        loc_str = "Cameroun"

    # Build description
    parts = []

    # Opening sentence — varies by property type
    prop_lower = prop_type.lower()
    if "chambre" in prop_lower:
        openers = [
            f"Chambre à louer dans la région de {loc_str}.",
            f"Belle chambre localisée à {loc_str}.",
            f"Chambre confortable disponible à {loc_str}.",
        ]
    elif "studio" in prop_lower:
        openers = [
            f"Studio moderne à louer à {loc_str}.",
            f"Studio situé à {loc_str}, idéal pour un étudiant ou un jeune actif.",
            f"Charmant studio disponible à {loc_str}.",
        ]
    elif "appartement" in prop_lower:
        if is_furnished:
            openers = [
                f"Appartement meublé à louer à {loc_str}.",
                f"Bel appartement meublé situé à {loc_str}.",
                f"Appartement meublé de qualité disponible à {loc_str}.",
            ]
        else:
            openers = [
                f"Appartement à louer à {loc_str}.",
                f"Bel appartement situé à {loc_str}.",
                f"Appartement disponible à {loc_str}.",
            ]
    elif "duplex" in prop_lower or "maison" in prop_lower:
        openers = [
            f"{prop_type} à louer à {loc_str}.",
            f"Belle ${prop_type.lower()} située à {loc_str}.",
            f"{prop_type} disponible à {loc_str}.",
        ]
    else:
        openers = [
            f"{prop_type} à louer à {loc_str}.",
            f"Bien immobilier disponible à {loc_str}.",
        ]

    # Pick opener deterministically by ID
    parts.append(openers[listing.id % len(openers)])

    # Bedrooms
    if bedrooms and bedrooms > 0:
        parts.append(f"Le bien comprend {bedrooms} chambre{'s' if bedrooms > 1 else ''}.")

    # Bathrooms
    if baths and str(baths).strip() and int(str(baths).strip()) > 0:
        try:
            b = int(str(baths).strip())
            parts.append(f"Il dispose de {b} salle{'s' if b > 1 else ''} de bain.")
        except (ValueError, TypeError):
            pass

    # Area
    if area and str(area).strip():
        try:
            a = float(str(area).strip())
            if 5 <= a <= 50000:
                parts.append(f"Surface de {int(a)} m².")
        except (ValueError, TypeError):
            pass

    # Furnished
    if is_furnished and "meublé" not in parts[0].lower():
        parts.append("Le logement est meublé et prêt à habiter.")

    # Titled land
    if is_titled:
        parts.append("Titre foncier en règle.")

    # Price
    price_str = _format_price(price)
    if price_str:
        parts.append(f"Loyer: {price_str} FCFA par mois.")

    # Closing
    closings = [
        "Contactez-nous pour organiser une visite.",
        "Disponible immédiatement, n'hésitez pas à réserver.",
        "Idéal pour un séjour confortable et sécurisé.",
        "Emplacement stratégique avec un accès facile aux commodités.",
    ]
    parts.append(closings[listing.id % len(closings)])

    return " ".join(parts)


def main():
    db = SessionLocal()
    try:
        kasastay = db.query(Source).filter(Source.slug == "kasastay").first()
        if not kasastay:
            print("Kasastay source not found")
            return

        listings = db.query(RawListing).filter(
            RawListing.source_id == kasastay.id,
        ).all()

        updated = 0
        for listing in listings:
            desc = listing.description_raw or ""
            if len(desc) >= 50:
                continue  # Already has a decent description

            loc_info = _parse_location_raw(listing.location_raw or "")
            new_desc = generate_description(listing, loc_info)

            print(f"  [{listing.id}] {listing.title_raw[:50]}")
            print(f"    OLD: {desc[:80]}")
            print(f"    NEW: {new_desc[:120]}")
            listing.description_raw = new_desc
            updated += 1

        db.commit()
        print(f"\n=== Updated {updated} Kasastay listings with enriched descriptions ===")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()