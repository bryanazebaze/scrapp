#!/usr/bin/env python3
"""Generate meaningful French descriptions for all 160 Mapiole listings.

The Mapiole scraper captured website boilerplate/template text instead of real
property descriptions. This script replaces that garbage with natural,
professional French real-estate descriptions derived from each listing's
title, property type, price, location, and payload data (bedrooms, bathrooms,
area, amenities).

Usage:
    cd /home/kelcy/Projects/Defence/scrapp
    python scripts/generate_mapiole_descriptions.py
"""
from __future__ import annotations

import re
import sys
import random
from pathlib import Path

# Ensure project root is on sys.path so `core` is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import SessionLocal
from core.models import RawListing, Source


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def format_price(price: int | None) -> str | None:
    """Format an integer price with space thousand separators, e.g. 120000000 -> '120 000 000 FCFA'."""
    if price is None or price <= 0:
        return None
    return f"{price:,}".replace(",", " ") + " FCFA"


def extract_area_from_title(title: str) -> float | None:
    """Try to find a surface area in the title (e.g. '299m2', '100 m²')."""
    m = re.search(r"(\d+)\s*m[2²]", title, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


def parse_title(title: str) -> dict:
    """Extract structured info from the listing title."""
    t_lower = title.lower().strip()

    info = {
        "action": None,        # "à louer" | "à vendre" | None
        "furnished": False,    # meublé
        "titled": False,       # titré
        "location": None,      # extracted location
        "city": None,          # extracted city
        "area_from_title": extract_area_from_title(title),
        "property_subtype": None,  # studio, chambre, appartement, etc.
    }

    # Action
    if "à louer" in t_lower or "a louer" in t_lower or "location de" in t_lower:
        info["action"] = "à louer"
    if "à vendre" in t_lower or "a vendre" in t_lower or "for sale" in t_lower:
        info["action"] = "à vendre"

    # Furnished
    if "meublé" in t_lower or "meublee" in t_lower or "meublée" in t_lower:
        info["furnished"] = True

    # Titled land
    if "titré" in t_lower or "titre foncier" in t_lower:
        info["titled"] = True

    # Property subtype from title
    if "studio" in t_lower:
        info["property_subtype"] = "studio"
    elif "chambre" in t_lower:
        info["property_subtype"] = "chambre"
    elif "appartement" in t_lower:
        info["property_subtype"] = "appartement"
    elif "maison" in t_lower:
        info["property_subtype"] = "maison"
    elif "terrain" in t_lower:
        info["property_subtype"] = "terrain"
    elif "bureau" in t_lower or "espace commercial" in t_lower or "commercial" in t_lower:
        info["property_subtype"] = "bureau"
    elif "hotel" in t_lower or "hôtel" in t_lower:
        info["property_subtype"] = "hotel"
    elif "salle de fête" in t_lower or "salle de fete" in t_lower:
        info["property_subtype"] = "salle"

    # Extract city from title
    for city in ["Yaoundé", "Yaounde", "Douala", "Bafoussam", "Bamenda",
                  "Kribi", "Limbé", "Limbe", "Edéa", "Edea", "Garoua",
                  "Maroua", "Buea", "Nkongsamba", "Mbankomo", "Mbang", "Moungo"]:
        if city.lower() in t_lower:
            info["city"] = city
            break

    # Extract location/neighborhood from title
    # Pattern: "X, Location, City" or "X à Location"
    # Try comma-separated parts
    parts = [p.strip() for p in title.split(",")]
    if len(parts) >= 2:
        # The part before the last is often the neighborhood
        candidate = parts[-2] if len(parts) >= 3 else parts[1]
        # Clean up: remove "à louer", "à vendre" etc.
        candidate = re.sub(r"\b(à|a)\s+(louer|vendre)\b", "", candidate, flags=re.IGNORECASE).strip()
        candidate = candidate.strip(" ,.-")
        if candidate and len(candidate) > 2 and candidate.lower() not in ("yaoundé", "yaounde", "douala"):
            info["location"] = candidate

    # Also try "près de X" pattern
    m = re.search(r"près de\s+(.+?)(?:,|$)", title, re.IGNORECASE)
    if m and not info["location"]:
        info["location"] = m.group(1).strip()

    # Try "à X" pattern for location (not "à louer"/"à vendre")
    m = re.search(r"\bà\s+([A-ZÀ-Ÿ][\w\s-]+?)(?:,|\.|$)", title)
    if m and not info["location"]:
        loc = m.group(1).strip()
        if loc.lower() not in ("louer", "vendre", "louer,", "vendre,"):
            info["location"] = loc

    return info


def get_location(listing, title_info: dict) -> str:
    """Determine the best location string for a listing."""
    # 1. location_raw if non-empty
    loc_raw = (listing.location_raw or "").strip()
    if loc_raw and len(loc_raw) > 2:
        return loc_raw
    # 2. From title parse
    if title_info["location"]:
        return title_info["location"]
    # 3. City from title
    if title_info["city"]:
        return title_info["city"]
    # 4. Try to extract from URL in payload
    payload = listing.payload or {}
    url = payload.get("url_source") or ""
    if url:
        # URL pattern: mapiole.com/City/Type/...
        parts = url.split("/")
        if len(parts) >= 4:
            city_from_url = parts[-3] if "mapiole.com" in url else None
            if city_from_url and city_from_url not in ("http:", "https:", ""):
                return city_from_url.replace("-", " ").strip()
    return ""


def get_area(listing, title_info: dict) -> float | None:
    """Get area in sqm from payload or title."""
    payload = listing.payload or {}
    area = payload.get("area_sqm")
    if area is None:
        # Try nested payload
        nested = payload.get("payload", {})
        if isinstance(nested, dict):
            area = nested.get("area_sqm")
    if area is None or area <= 0:
        area = title_info.get("area_from_title")
    if area is None or area <= 0 or area > 999999:
        return None
    return float(area)


def get_bedrooms(listing) -> int:
    payload = listing.payload or {}
    b = payload.get("bedrooms")
    if b is None:
        nested = payload.get("payload", {})
        if isinstance(nested, dict):
            b = nested.get("bedrooms")
    return int(b) if b and int(b) > 0 else 0


def get_bathrooms(listing) -> int:
    payload = listing.payload or {}
    b = payload.get("bathrooms")
    if b is None:
        nested = payload.get("payload", {})
        if isinstance(nested, dict):
            b = nested.get("bathrooms")
    return int(b) if b and int(b) > 0 else 0


def get_amenities(listing) -> list[str]:
    payload = listing.payload or {}
    a = payload.get("amenities")
    if a is None:
        nested = payload.get("payload", {})
        if isinstance(nested, dict):
            a = nested.get("amenities")
    if not a or not isinstance(a, list):
        return []
    return [str(x) for x in a if x]


def format_area(area: float) -> str:
    """Format area as '299 m²' or '1 000 m²'."""
    if area == int(area):
        return f"{int(area):,}".replace(",", " ") + " m²"
    return f"{area:,}".replace(",", " ") + " m²"


# Amenity translation to French
AMENITY_FR = {
    "Air Conditioning": "climatisation",
    "Dryer": "sèche-linge",
    "Gym": "salle de sport",
    "Laundry": "buanderie",
    "Microwave": "micro-ondes",
    "Outdoor Shower": "douche extérieure",
    "Refrigerator": "réfrigérateur",
    "TV Cable": "télévision par câble",
    "Washer": "lave-linge",
    "WiFi": "connexion WiFi",
    "Window Coverings": "rideaux et stores",
    "Parking": "parking",
    "Pool": "piscine",
    "Garden": "jardin",
    "Security": "sécurité 24h/24",
}


def amenities_to_french(amenities: list[str]) -> str:
    """Translate amenity list to a French phrase."""
    fr_list = []
    for a in amenities:
        fr = AMENITY_FR.get(a, a.lower())
        fr_list.append(fr)
    if not fr_list:
        return ""
    if len(fr_list) == 1:
        return fr_list[0]
    if len(fr_list) == 2:
        return f"{fr_list[0]} et {fr_list[1]}"
    return ", ".join(fr_list[:-1]) + f" et {fr_list[-1]}"


# --------------------------------------------------------------------------- #
# Description generators
# --------------------------------------------------------------------------- #

# Varying sentence fragments to avoid identical descriptions
TERRAIN_OPENINGS = [
    "Terrain {action} {location}.",
    "Belle parcelle {action} {location}.",
    "Parcelle de {area} {action} {location}.",
    "Terrain disponible {action} {location}.",
    "Opportunité foncière {action} {location}.",
]

TERRAIN_TITLED = [
    "Titre foncier sécurisé, idéal pour un projet de construction ou d'investissement.",
    "Parcelle bornée avec titre foncier en règle, prête à être exploitée.",
    "Terrain titré offrant une sécurité juridique totale pour votre investissement.",
]

TERRAIN_UNTITLED = [
    "Zone bien desservie avec un accès aux commodités et voies de circulation.",
    "Terrain bien situé, proche des infrastructures et commodités de la région.",
    "Environnement calme et accessible, favorable à un aménagement résidentiel ou commercial.",
]

TERRAIN_AREA = [
    "D'une superficie de {area}, ce terrain offre un excellent potentiel d'aménagement.",
    "La parcelle couvre {area}, offrant un espace généreux pour vos projets.",
    "Vaste terrain de {area} avec de multiples possibilités de développement.",
]

TERRAIN_LARGE = [
    "Vaste étendue idéale pour des projets agricoles, immobiliers ou de développement.",
    "Grande parcelle offrant un potentiel remarquable pour des projets à grande échelle.",
    "Surface étendue permettant divers projets: agriculture, lotissement ou investissement.",
]

APPART_OPENINGS = [
    "{subtype} {action} {location}.",
    "{subtype} {furnished_label}{action} {location}.",
    "Découvrez ce {subtype} {action} {location}.",
    "{subtype} disponible {action} {location}.",
]

APPART_AREA = [
    "Avec une surface de {area}, ce bien offre un espace de vie confortable.",
    "Le logement dispose de {area}, optimisant chaque mètre carré.",
    "D'une superficie de {area}, l'aménagement permet une circulation agréable.",
]

APPART_BEDROOMS = [
    "Il compte {bedrooms} chambre(s) et {bathrooms} salle(s) de bain.",
    "Le bien comprend {bedrooms} chambre(s) ainsi que {bathrooms} salle(s) de bain.",
    "Il offre {bedrooms} chambre(s) et {bathrooms} salle(s) de bain pour un quotidien pratique.",
]

APPART_AMENITIES = [
    "Les équipements incluent: {amenities}.",
    "Le bien est doté de: {amenities}.",
    "Vous bénéficiez de plusieurs équipements: {amenities}.",
]

APPART_LOCATION = [
    "L'emplacement à {location} garantit un accès facile aux commerces, écoles et transports.",
    "Situé à {location}, ce logement profite d'un quartier dynamique et bien desservi.",
    "Le quartier de {location} offre un cadre de vie agréable avec toutes les commodités à proximité.",
]

APPART_GENERIC = [
    "Idéal pour une personne seule, un couple ou un étudiant cherchant un logement pratique.",
    "Ce logement convient parfaitement à une recherche de confort et de proximité urbaine.",
    "Un compromis idéal entre confort, fonctionnalité et accessibilité.",
    "Parfait pour quiconque recherche un habitat fonctionnel dans un secteur recherché.",
]

CHAMBRE_OPENINGS = [
    "Chambre {furnished_label}{action} {location}.",
    "Chambre {action} {location}, idéale pour un étudiant ou un jeune actif.",
    "Belle chambre {action} {location}.",
    "Chambre disponible {action} {location}.",
]

CHAMBRE_AMENITIES = [
    "La chambre est équipée de: {amenities}.",
    "Elle dispose de plusieurs équipements: {amenities}.",
    "Le confort est assuré par: {amenities}.",
]

CHAMBRE_GENERIC = [
    "Idéale pour un étudiant ou un jeune professionnel en quête d'un logement abordable.",
    "Un logement pratique et économique, parfait pour une occupation individuelle.",
    "Solution d'hébergement économique et bien située pour une personne seule.",
    "Cadre idéal pour un séjour court ou long à un tarif compétitif.",
]

MAISON_OPENINGS = [
    "Maison {action} {location}.",
    "Belle maison {action} {location}.",
    "Maison {furnished_label}{action} {location}.",
]

MAISON_AREA = [
    "La superficie de {area} permet un aménagement polyvalent selon vos besoins.",
    "Avec {area}, la propriété offre un espace généreux pour toute la famille.",
    "D'une surface de {area}, cette maison s'adapte à de multiples configurations.",
]

BUREAU_OPENINGS = [
    "Espace commercial {action} {location}.",
    "Local professionnel {action} {location}.",
    "Bureau {action} {location}, idéal pour entreprise ou commerce.",
]

BUREAU_AREA = [
    "L'espace de {area} permet d'accueillir plusieurs postes de travail ou activités.",
    "Avec une superficie de {area}, ce local offre une grande flexibilité d'aménagement.",
    "D'une surface de {area}, il convient à des bureaux, un showroom ou un entrepôt.",
]

BUREAU_GENERIC = [
    "Idéal pour une entreprise cherchant un emplacement stratégique et visible.",
    "Parfait pour un commerce, une agence ou des bureaux professionnels.",
    "Un emplacement de choix pour développer votre activité professionnelle.",
]

HOTEL_OPENINGS = [
    "Hôtel {action} {location}.",
    "Établissement hôtelier {action} {location}.",
]

HOTEL_GENERIC = [
    "L'établissement propose un service de qualité avec des chambres confortables et modernes.",
    "Idéal pour un séjour court ou long, avec un service adapté aux voyageurs d'affaires ou de loisirs.",
    "Un cadre accueillant et équipé pour offrir un excellent confort aux hôtes.",
]

SALLE_OPENINGS = [
    "Salle de fête {action} {location}.",
    "Salle de réception {action} {location}.",
]

SALLE_GENERIC = [
    "Idéale pour organiser cérémonies, mariages, séminaires et autres grands événements.",
    "Un espace spacieux et équipé pour accueillir vos célébrations dans les meilleures conditions.",
    "Parfait pour des événements privés ou professionnels dans un cadre adapté.",
]

OTHER_OPENINGS = [
    "Bien immobilier {action} {location}.",
    "Propriété {action} {location}.",
]


def pick(lst: list[str], seed: int) -> str:
    """Pick an element from a list deterministically based on a seed (listing id)."""
    return lst[seed % len(lst)]


def generate_description(listing) -> str:
    """Generate a natural French description for a single listing."""
    title = listing.title_raw or ""
    title_info = parse_title(title)
    prop_type = (listing.property_type_raw or "").strip()
    price = listing.price_parsed or 0
    location = get_location(listing, title_info)
    area = get_area(listing, title_info)
    bedrooms = get_bedrooms(listing)
    bathrooms = get_bathrooms(listing)
    amenities = get_amenities(listing)

    # Determine action from title or infer
    action = title_info["action"]
    if not action:
        if "louer" in title.lower() or "location" in title.lower():
            action = "à louer"
        elif "vendre" in title.lower() or "for sale" in title.lower():
            action = "à vendre"
        elif prop_type == "Terrain":
            action = "à vendre"
        elif prop_type in ("Appartement", "Chambre"):
            action = "à louer"
        else:
            action = "à louer"

    # Subtype label
    subtype = title_info["property_subtype"]
    if subtype == "studio":
        subtype_label = "studio"
    elif subtype == "chambre":
        subtype_label = "chambre"
    elif subtype == "appartement":
        subtype_label = "appartement"
    elif subtype == "maison":
        subtype_label = "maison"
    elif subtype == "bureau":
        subtype_label = "espace commercial"
    elif subtype == "hotel":
        subtype_label = "hôtel"
    elif subtype == "salle":
        subtype_label = "salle de fête"
    elif subtype == "terrain":
        subtype_label = "terrain"
    else:
        subtype_label = prop_type.lower() if prop_type else "bien immobilier"

    furnished_label = "meublé " if title_info["furnished"] else ""
    loc_str = f"à {location}" if location else ""
    seed = int(listing.id) if listing.id else 0

    # Build property-type-specific description
    sentences = []

    if prop_type == "Terrain" or subtype == "terrain":
        # Opening
        opening = pick(TERRAIN_OPENINGS, seed)
        if "{area}" in opening and area:
            opening = opening.format(area=format_area(area), action=action, location=loc_str)
        else:
            opening = opening.format(action=action, location=loc_str)
        sentences.append(opening)

        # Titled land info
        if title_info["titled"]:
            sentences.append(pick(TERRAIN_TITLED, seed))
        else:
            sentences.append(pick(TERRAIN_UNTITLED, seed))

        # Area detail (if not already mentioned in opening)
        if area and "{area}" not in pick(TERRAIN_OPENINGS, seed):
            if area >= 10000:
                sentences.append(pick(TERRAIN_LARGE, seed))
            else:
                area_sentence = pick(TERRAIN_AREA, seed).format(area=format_area(area))
                sentences.append(area_sentence)

        # Price
        price_str = format_price(price)
        if price_str:
            sentences.append(f"Prix: {price_str}.")
        else:
            sentences.append("Contactez-nous pour plus d'informations sur le prix.")

    elif prop_type == "Chambre" or subtype == "chambre":
        opening = pick(CHAMBRE_OPENINGS, seed)
        opening = opening.format(
            furnished_label=furnished_label,
            action=action,
            location=loc_str,
        )
        sentences.append(opening)

        # Area
        if area and area > 0:
            sentences.append(f"Surface de {format_area(area)}.")

        # Amenities
        if amenities:
            amenity_str = amenities_to_french(amenities)
            sentences.append(pick(CHAMBRE_AMENITIES, seed).format(amenities=amenity_str))

        # Generic
        sentences.append(pick(CHAMBRE_GENERIC, seed))

        # Price
        price_str = format_price(price)
        if price_str:
            sentences.append(f"Loyer: {price_str} par mois.")

    elif prop_type == "Appartement" or subtype in ("studio", "appartement"):
        opening = pick(APPART_OPENINGS, seed)
        opening = opening.format(
            subtype=subtype_label,
            furnished_label=furnished_label,
            action=action,
            location=loc_str,
        )
        sentences.append(opening)

        # Bedrooms/bathrooms
        if bedrooms > 0 or bathrooms > 0:
            parts = []
            if bedrooms > 0:
                bed_str = f"{bedrooms} chambre" + ("s" if bedrooms > 1 else "")
                parts.append(bed_str)
            if bathrooms > 0:
                bath_str = f"{bathrooms} salle de bain" + ("s" if bathrooms > 1 else "")
                parts.append(bath_str)
            if parts:
                sentences.append(f"Le bien comprend {' et '.join(parts)}.")

        # Area
        if area and area > 0:
            sentences.append(pick(APPART_AREA, seed).format(area=format_area(area)))

        # Amenities
        if amenities:
            amenity_str = amenities_to_french(amenities)
            sentences.append(pick(APPART_AMENITIES, seed).format(amenities=amenity_str))

        # Location benefit
        if location:
            sentences.append(pick(APPART_LOCATION, seed).format(location=location))

        # Generic closing
        sentences.append(pick(APPART_GENERIC, seed))

        # Price
        price_str = format_price(price)
        if price_str:
            if action == "à louer":
                sentences.append(f"Loyer: {price_str} par mois.")
            else:
                sentences.append(f"Prix: {price_str}.")

    elif prop_type == "Maison" or subtype == "maison":
        opening = pick(MAISON_OPENINGS, seed)
        opening = opening.format(
            furnished_label=furnished_label,
            action=action,
            location=loc_str,
        )
        sentences.append(opening)

        # Bedrooms/bathrooms
        if bedrooms > 0 or bathrooms > 0:
            parts = []
            if bedrooms > 0:
                bed_str = f"{bedrooms} chambre" + ("s" if bedrooms > 1 else "")
                parts.append(bed_str)
            if bathrooms > 0:
                bath_str = f"{bathrooms} salle de bain" + ("s" if bathrooms > 1 else "")
                parts.append(bath_str)
            if parts:
                sentences.append(f"La maison comprend {' et '.join(parts)}.")

        # Area
        if area and area > 0:
            sentences.append(pick(MAISON_AREA, seed).format(area=format_area(area)))

        # Amenities
        if amenities:
            amenity_str = amenities_to_french(amenities)
            sentences.append(f"Équipements: {amenity_str}.")

        # Price
        price_str = format_price(price)
        if price_str:
            if action == "à louer":
                sentences.append(f"Loyer: {price_str} par mois.")
            else:
                sentences.append(f"Prix: {price_str}.")

    elif prop_type == "Bureau" or subtype == "bureau":
        opening = pick(BUREAU_OPENINGS, seed)
        opening = opening.format(action=action, location=loc_str)
        sentences.append(opening)

        # Area
        if area and area > 0:
            sentences.append(pick(BUREAU_AREA, seed).format(area=format_area(area)))

        # Generic
        sentences.append(pick(BUREAU_GENERIC, seed))

        # Price
        price_str = format_price(price)
        if price_str:
            if action == "à louer":
                sentences.append(f"Loyer: {price_str} par mois.")
            else:
                sentences.append(f"Prix: {price_str}.")

    elif prop_type == "Autre":
        if subtype == "hotel":
            opening = pick(HOTEL_OPENINGS, seed)
            opening = opening.format(action=action, location=loc_str)
            sentences.append(opening)

            # Amenities for hotels
            if amenities:
                amenity_str = amenities_to_french(amenities)
                sentences.append(f"Les équipements de l'établissement incluent: {amenity_str}.")

            if area and area > 0:
                sentences.append(f"L'établissement s'étend sur {format_area(area)}.")

            sentences.append(pick(HOTEL_GENERIC, seed))

            price_str = format_price(price)
            if price_str:
                sentences.append(f"Tarif: {price_str} par jour.")

        elif subtype == "salle":
            opening = pick(SALLE_OPENINGS, seed)
            opening = opening.format(action=action, location=loc_str)
            sentences.append(opening)

            if amenities:
                amenity_str = amenities_to_french(amenities)
                sentences.append(f"Équipements: {amenity_str}.")

            sentences.append(pick(SALLE_GENERIC, seed))

            price_str = format_price(price)
            if price_str:
                sentences.append(f"Tarif: {price_str}.")

        else:
            # Generic "Autre"
            opening = pick(OTHER_OPENINGS, seed)
            opening = opening.format(action=action, location=loc_str)
            sentences.append(opening)

            if area and area > 0:
                sentences.append(f"Surface de {format_area(area)}.")

            if amenities:
                amenity_str = amenities_to_french(amenities)
                sentences.append(f"Équipements: {amenity_str}.")

            price_str = format_price(price)
            if price_str:
                sentences.append(f"Prix: {price_str}.")
    else:
        # Fallback
        opening = pick(OTHER_OPENINGS, seed)
        opening = opening.format(action=action, location=loc_str)
        sentences.append(opening)

        if area and area > 0:
            sentences.append(f"Surface de {format_area(area)}.")

        if bedrooms > 0:
            bed_label = f"{bedrooms} chambre" + ("s" if bedrooms > 1 else "")
            sentences.append(f"{bed_label} disponible" + ("s" if bedrooms > 1 else "") + ".")

        if amenities:
            amenity_str = amenities_to_french(amenities)
            sentences.append(f"Équipements: {amenity_str}.")

        price_str = format_price(price)
        if price_str:
            sentences.append(f"Prix: {price_str}.")

    # Join sentences
    description = " ".join(sentences)
    # Clean up any double spaces
    description = re.sub(r"\s+", " ", description).strip()
    return description


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    db = SessionLocal()
    try:
        # Find the Mapiole source
        source = db.query(Source).filter(Source.slug == "mapiole").first()
        if not source:
            print("ERROR: Source 'mapiole' not found in database.")
            return

        # Query all Mapiole raw listings
        listings = (
            db.query(RawListing)
            .filter(RawListing.source_id == source.id)
            .order_by(RawListing.id)
            .all()
        )
        print(f"Found {len(listings)} Mapiole listings to update.\n")

        updated = 0
        for listing in listings:
            new_desc = generate_description(listing)
            if new_desc:
                listing.description_raw = new_desc
                updated += 1
                # Print summary for first 20 and every 20th after
                if updated <= 20 or updated % 20 == 0:
                    preview = new_desc[:100]
                    print(f"  [{listing.id:>4}] {listing.title_raw[:60]}")
                    print(f"        -> {preview}...")
                    print()
            else:
                print(f"  [{listing.id:>4}] SKIP - could not generate description for: {listing.title_raw}")

        print(f"\n{'='*70}")
        print(f"Updated {updated}/{len(listings)} listings.")
        print("Committing to database...")

        db.commit()
        print("Done. Transaction committed successfully.")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()