#!/usr/bin/env python3
"""Clean boilerplate from Kasastay listing descriptions.

Every Kasastay description is wrapped in website template text:
  [header boilerplate]
  Copyright©2026EL&L Bright Properties LLC.Tous droits réservés.
  [REAL DESCRIPTION]
  [footer boilerplate: Pas encore d'avis / host name / Hôte vérifié /
   Planifier une visite / D'autres logements / nearby location strings]

This script extracts the real description and updates description_raw directly.
If the cleaned text is empty or very short (< 15 chars), falls back to title_raw.
"""

import re
import sys

# Ensure project root is on sys.path so `core` package is importable
sys.path.insert(0, "/home/kelcy/Projects/Defence/scrapp")

from core.database import SessionLocal
from core.models import RawListing, Source


# --- Markers --------------------------------------------------------------- #

HEADER_MARKER = "Copyright"          # The Copyright line marks end of header boilerplate

FOOTER_MARKERS = [
    "Pas encore d'avis",
    "Planifier une visite",
    "D'autres logements",
    "Hôte vérifié",
]

# Location suggestion lines contain these patterns
LOCATION_PATTERNS = [
    r"Cameroun,\s*Wouri",
    r"Cameroun,\s*Mfoundi",
    r"Méfou-et-Akono",
    r"Djoungolo",
    r"Simbock",
    r"Logpom",
    r"BELGOCAM",
    r"Commissariat\s*\d+",
    r"Unnamed Road",
    r"Bonaboussad",
    r"Bonamoussad",
    r"Bonabéri",
]

# Real-estate keywords that indicate a line is actual description content
RE_KEYWORDS = [
    "chambre", "salon", "cuisine", "douche", "parking", "studio", "appartement",
    "maison", "villa", "terrain", "prix", "loyer", "standing", "sécurisé",
    "sécurise", "meublé", "non meublé", "résidence", "étage", "wc", "eau",
    "placard", "fourrage", "compteur", "jardin", "balcon", "terrasse", "ascenseur",
    "garage", "bureau", "magasin", "shop", "commercial", "habitation", "locataire",
    "bail", "caution", "mois", "jour", " nuit", "séjour", "vacances", "voyage",
    " quartier", "camp", "école", "hôpital", "marché", "route", "avenue",
    "salle à manger", "salle de bain", "chambre", "douches", "chaude",
    "séjourner", "partager", "expérience", "hôte", "visite",
    "grand", "vaste", "spacieux", "lumineux", "moderne", "neuf", "rénové",
    "F2", "F3", "F4", "F5", "T1", "T2", "T3", "T4", "T5",
    "m²", "m2", "surface", "superficie",
]

# Compile location patterns into a single regex
LOCATION_RE = re.compile("|".join(LOCATION_PATTERNS), re.IGNORECASE)


def is_location_line(line: str) -> bool:
    """Check if a line is a nearby-location suggestion (template artifact)."""
    stripped = line.strip()
    if not stripped:
        return False
    return bool(LOCATION_RE.search(stripped))


def is_host_name_line(line: str, in_footer: bool) -> bool:
    """Heuristic: short line with no real-estate keywords, appearing in footer area."""
    stripped = line.strip()
    if not stripped:
        return False
    if not in_footer:
        return False
    # Host name lines are typically < 60 chars, no numbers (except maybe periods)
    if len(stripped) > 60:
        return False
    # Check if it contains any real-estate keywords
    lower = stripped.lower()
    for kw in RE_KEYWORDS:
        if kw in lower:
            return False
    # If it looks like a person's name (2-4 words, mostly alphabetic)
    words = stripped.split()
    if 1 <= len(words) <= 5:
        alpha_ratio = sum(c.isalpha() or c in ".-'" for c in stripped) / len(stripped)
        if alpha_ratio > 0.8:
            return True
    return False


def is_boilerplate_line(line: str) -> bool:
    """Check if a standalone line is pure boilerplate (header/footer template text)."""
    stripped = line.strip()
    if not stripped:
        return True
    boilerplate_phrases = [
        "Newsletter mensuelle",
        "Nouvelles annonces et astuces voyage",
        "Devenir hôte",
        "Rentabilisez votre logement",
        "Trouvez votre logement idéal au Cameroun",
        "Copyright",
        "Bright Properties",
        "Tous droits réservés",
        "Pas encore d'avis",
        "Hôte vérifié",
        "Planifier une visite",
        "Choisissez une date",
        "D'autres logements",
    ]
    for phrase in boilerplate_phrases:
        if phrase in stripped:
            return True
    return False


def clean_description(raw_desc: str, title: str) -> str:
    """Extract the real description from boilerplate-wrapped text.

    Strategy:
    1. Split into lines.
    2. Find the Copyright line — everything after it is candidate content.
    3. Find the first footer marker — everything before it (within candidate) is the real desc.
    4. Remove remaining boilerplate lines, location lines, and host name lines.
    5. Join and strip. If empty or < 15 chars, fall back to title.
    """
    if not raw_desc:
        return title

    lines = raw_desc.split("\n")

    # --- Step 1: Find the Copyright line (end of header boilerplate) ---
    copyright_idx = None
    for i, line in enumerate(lines):
        if HEADER_MARKER in line and "Bright Properties" in line:
            copyright_idx = i
            break
        # Also match the exact string without requiring both parts
        if "Copyright" in line and "Tous droits réservés" in line:
            copyright_idx = i
            break

    if copyright_idx is not None:
        # Everything after the Copyright line is candidate content
        candidate_lines = lines[copyright_idx + 1:]
    else:
        # No Copyright marker found — try to work with the full text
        candidate_lines = lines[:]

    # --- Step 2: Find the first footer marker within candidate lines ---
    footer_idx = None
    for i, line in enumerate(candidate_lines):
        stripped = line.strip()
        for marker in FOOTER_MARKERS:
            if marker in stripped:
                footer_idx = i
                break
        if footer_idx is not None:
            break

    if footer_idx is not None:
        real_lines = candidate_lines[:footer_idx]
    else:
        real_lines = candidate_lines[:]

    # --- Step 3: Remove remaining boilerplate, location, and host name lines ---
    # We need to track whether we're past the footer for host-name detection.
    # Since we already truncated at the first footer marker, any remaining
    # boilerplate lines should be filtered. But there might be stray host name
    # lines that slipped in before the footer marker. Use is_boilerplate_line.
    cleaned = []
    for line in real_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if is_boilerplate_line(stripped):
            continue
        if is_location_line(stripped):
            continue
        # Host name lines: short, no keywords, no numbers — likely a name
        # We check this only if the line doesn't look like real content
        lower = stripped.lower()
        has_keyword = any(kw in lower for kw in RE_KEYWORDS)
        has_number = any(c.isdigit() for c in stripped)
        if not has_keyword and not has_number and len(stripped) < 60:
            # Could be a host name that appeared before the footer marker
            # But it could also be a legit short description line.
            # Only filter if it looks like a name: mostly alpha, 1-5 words
            words = stripped.split()
            if 1 <= len(words) <= 5:
                alpha_ratio = sum(c.isalpha() or c in ".-'" for c in stripped) / len(stripped)
                if alpha_ratio > 0.85:
                    continue  # Skip — likely a host name
        cleaned.append(stripped)

    result = "\n".join(cleaned).strip()

    # --- Step 4: Fallback if empty or too short ---
    if len(result) < 15:
        return title

    return result


def main():
    db = SessionLocal()
    try:
        # Find the Kasastay source
        source = db.query(Source).filter(Source.slug == "kasastay").first()
        if not source:
            print("ERROR: No source with slug 'kasastay' found.")
            return

        # Query all raw_listings for Kasastay
        listings = (
            db.query(RawListing)
            .filter(RawListing.source_id == source.id)
            .order_by(RawListing.id)
            .all()
        )

        print(f"Found {len(listings)} Kasastay listings to clean.\n")
        print("=" * 100)

        updated = 0
        fallback = 0
        no_change = 0

        for listing in listings:
            original = listing.description_raw or ""
            title = listing.title_raw or ""

            cleaned = clean_description(original, title)

            # Determine what happened
            used_fallback = len(cleaned) == len(title) and cleaned == title and original != title
            changed = cleaned != original.strip()

            if changed:
                listing.description_raw = cleaned
                updated += 1
                if used_fallback:
                    fallback += 1
            else:
                no_change += 1

            # Print before/after
            print(f"\n--- Listing ID {listing.id} | {title[:60]}")
            print(f"  BEFORE ({len(original)} chars): {repr(original[:200])}{'...' if len(original) > 200 else ''}")
            print(f"  AFTER  ({len(cleaned)} chars): {repr(cleaned[:200])}{'...' if len(cleaned) > 200 else ''}")
            if used_fallback:
                print(f"  >> FELL BACK TO TITLE (cleaned text was too short)")
            elif not changed:
                print(f"  >> NO CHANGE")

        print("\n" + "=" * 100)
        print(f"\nSummary:")
        print(f"  Total listings:  {len(listings)}")
        print(f"  Updated:         {updated}")
        print(f"    - Cleaned:     {updated - fallback}")
        print(f"    - Fallback:    {fallback}")
        print(f"  No change:       {no_change}")

        if updated > 0:
            db.commit()
            print(f"\nCommitted {updated} updates to the database.")
        else:
            print(f"\nNo changes to commit.")
            db.rollback()

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()