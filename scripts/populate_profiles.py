"""Populate city_profiles and neighborhood_profiles from research data files.

Reads the structured Python dicts produced by the research agents from /tmp/
and inserts them into the database. Safe to re-run (upserts on unique keys).

Usage:
    python scripts/populate_profiles.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.database import SessionLocal
from core.models import CityProfile, NeighborhoodProfile, Location


# --------------------------------------------------------------------------- #
# Research data loaders
# --------------------------------------------------------------------------- #
def _load_module(file_path: str):
    """Load a Python file as a module and return it."""
    spec = importlib.util.spec_from_file_location("research_data", file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_research_files():
    """Load all research output files from /tmp/.

    Returns a dict: { "Douala": (city_profile, [nbh_profiles]), ... }
    """
    research_files = {
        # file -> (loader function name, cities covered)
        "/tmp/research_douala.py": ("douala",),
        "/tmp/research_yaounde.py": ("yaounde",),
        "/tmp/research_anglophone.py": ("anglophone",),
        "/tmp/research_north.py": ("north",),
        "/tmp/research_south.py": ("south",),
    }

    all_cities = {}  # city_name -> (city_profile_dict, [nbh_profile_dicts])

    for file_path, loaders in research_files.items():
        if not os.path.exists(file_path):
            print(f"  SKIP {file_path} (not found)")
            continue
        print(f"  Loading {file_path}")
        mod = _load_module(file_path)

        # Different research files have different structures
        if "douala" in loaders:
            if hasattr(mod, "CITY_PROFILE"):
                all_cities["Douala"] = (mod.CITY_PROFILE,
                                        getattr(mod, "NEIGHBORHOOD_PROFILES", []))
        elif "yaounde" in loaders:
            if hasattr(mod, "CITY_PROFILE"):
                all_cities["Yaoundé"] = (mod.CITY_PROFILE,
                                         getattr(mod, "NEIGHBORHOOD_PROFILES", []))
        elif "anglophone" in loaders:
            # Structure: CITIES = {"Bamenda": {...}, "Buea": {...}, "Limbe": {...}}
            # NEIGHBORHOODS = {"Bamenda": [...], ...}
            if hasattr(mod, "CITIES"):
                cities_dict = mod.CITIES
                neighborhoods_dict = getattr(mod, "NEIGHBORHOODS", {})
                for city_name, city_prof in cities_dict.items():
                    nbh_list = neighborhoods_dict.get(city_name, [])
                    all_cities[city_name] = (city_prof, nbh_list)
        elif "north" in loaders:
            if hasattr(mod, "CITIES"):
                cities_dict = mod.CITIES
                neighborhoods_dict = getattr(mod, "NEIGHBORHOODS", {})
                for city_name, city_prof in cities_dict.items():
                    nbh_list = neighborhoods_dict.get(city_name, [])
                    all_cities[city_name] = (city_prof, nbh_list)
        elif "south" in loaders:
            if hasattr(mod, "CITIES"):
                cities_dict = mod.CITIES
                neighborhoods_dict = getattr(mod, "NEIGHBORHOODS", {})
                for city_name, city_prof in cities_dict.items():
                    nbh_list = neighborhoods_dict.get(city_name, [])
                    all_cities[city_name] = (city_prof, nbh_list)

    return all_cities


# --------------------------------------------------------------------------- #
# Type coercion helpers
# --------------------------------------------------------------------------- #
import re as _re


def _coerce_population(val):
    """Extract an integer population from a value that might be a string.
    Takes only the FIRST number found to avoid concatenating multiple numbers."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        result = int(val)
        # Cap at 32-bit integer max for safety
        return result if result < 2_147_483_647 else None
    if isinstance(val, str):
        # Try to find "4.85 million" or "2.1 million"
        m = _re.search(r'([\d.,]+)\s*million', val, _re.IGNORECASE)
        if m:
            result = int(float(m.group(1).replace(',', '')) * 1_000_000)
            return result if result < 2_147_483_647 else None
        m = _re.search(r'([\d.,]+)\s*(?:billion|milliard)', val, _re.IGNORECASE)
        if m:
            result = int(float(m.group(1).replace(',', '')) * 1_000_000_000)
            return result if result < 2_147_483_647 else None
        # Find the first standalone number with thousand separators (e.g. "120,000")
        m = _re.search(r'(\d{1,3}(?:[,.]\d{3})+)', val)
        if m:
            digits = _re.sub(r'[^\d]', '', m.group(1))
            try:
                result = int(digits)
                return result if result < 2_147_483_647 else None
            except ValueError:
                pass
        # Find first simple number (6+ digits, to avoid matching years etc.)
        m = _re.search(r'(\d{6,})', val)
        if m:
            try:
                result = int(m.group(1))
                return result if result < 2_147_483_647 else None
            except ValueError:
                pass
        # Find first 5-digit number (small towns)
        m = _re.search(r'(\d{5})', val)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None


def _coerce_text(val):
    """Ensure a value is a string (join lists with newlines)."""
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, (list, tuple)):
        return "\n\n".join(str(v) for v in val if v)
    return str(val)


def _coerce_json(val):
    """Ensure a value is JSONB-serializable (pass through lists/dicts)."""
    if val is None:
        return None
    if isinstance(val, (list, dict)):
        return val
    if isinstance(val, str):
        # Try to parse as JSON, otherwise wrap in a list
        import json
        try:
            return json.loads(val)
        except (json.JSONDecodeError, ValueError):
            return [val] if val else None
    return val


# --------------------------------------------------------------------------- #
# DB upsert helpers
# --------------------------------------------------------------------------- #
def upsert_city_profile(db, city_name: str, profile: dict) -> CityProfile:
    """Insert or update a city profile."""
    existing = db.query(CityProfile).filter(
        CityProfile.city == city_name
    ).first()

    fields = {
        "region": _coerce_text(profile.get("region")),
        "security_rating": _coerce_text(profile.get("security_rating")),
        "security_summary": _coerce_text(profile.get("security_summary")),
        "current_threats": _coerce_json(profile.get("current_threats")),
        "safest_zones": _coerce_json(profile.get("safest_zones")),
        "emergency_contacts": _coerce_json(profile.get("emergency_contacts")),
        "travel_tips": _coerce_text(profile.get("travel_tips")),
        "curfew_info": _coerce_text(profile.get("curfew_info")),
        "population": _coerce_population(profile.get("population")),
        "area_description": _coerce_text(profile.get("area_description")),
    }

    if existing:
        for k, v in fields.items():
            if v is not None:
                setattr(existing, k, v)
        db.flush()
        return existing
    else:
        cp = CityProfile(city=city_name, **fields)
        db.add(cp)
        db.flush()
        return cp


def _find_location_id(db, city: str, neighborhood: str | None) -> int | None:
    """Find the location_id for a (city, neighborhood) pair."""
    if neighborhood:
        loc = db.query(Location).filter(
            Location.city == city,
            Location.neighborhood == neighborhood
        ).first()
        if loc:
            return loc.id
        # Try case-insensitive / accent-insensitive match
        from scrapers.utils import normalize_text
        n_norm = normalize_text(neighborhood)
        candidates = db.query(Location).filter(
            Location.city == city,
            Location.neighborhood.isnot(None)
        ).all()
        for c in candidates:
            if normalize_text(c.neighborhood) == n_norm:
                return c.id
    else:
        # City-wide location (neighborhood IS NULL)
        loc = db.query(Location).filter(
            Location.city == city,
            Location.neighborhood.is_(None)
        ).first()
        if loc:
            return loc.id
    return None


def upsert_neighborhood_profile(db, city: str, neighborhood: str | None,
                                profile: dict) -> NeighborhoodProfile:
    """Insert or update a neighborhood profile."""
    # Find matching location_id
    location_id = _find_location_id(db, city, neighborhood)

    # Check existing by (city, neighborhood) unique constraint
    query = db.query(NeighborhoodProfile).filter(
        NeighborhoodProfile.city == city
    )
    if neighborhood:
        query = query.filter(NeighborhoodProfile.neighborhood == neighborhood)
    else:
        query = query.filter(NeighborhoodProfile.neighborhood.is_(None))
    existing = query.first()

    fields = {
        "location_id": location_id,
        "security_rating": _coerce_text(profile.get("security_rating")),
        "security_notes": _coerce_text(profile.get("security_notes")),
        "amenities": _coerce_json(profile.get("amenities")),
        "transport_info": _coerce_text(profile.get("transport_info")),
        "real_estate_context": _coerce_text(profile.get("real_estate_context")),
        "demographics": _coerce_text(profile.get("demographics")),
        "landmarks": _coerce_json(profile.get("landmarks")),
        "risk_factors": _coerce_json(profile.get("risk_factors")),
        "description": _coerce_text(profile.get("description")),
    }

    if existing:
        for k, v in fields.items():
            if v is not None:
                setattr(existing, k, v)
        db.flush()
        return existing
    else:
        np = NeighborhoodProfile(
            city=city,
            neighborhood=neighborhood,
            **fields
        )
        db.add(np)
        db.flush()
        return np


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    print("=== Loading research data ===")
    all_cities = load_research_files()

    if not all_cities:
        print("No research data found. Run the research agents first.")
        return

    print(f"\n=== Found data for {len(all_cities)} cities ===")
    for city, (city_prof, nbh_list) in all_cities.items():
        print(f"  {city}: {len(nbh_list)} neighborhoods")

    db = SessionLocal()
    try:
        city_count = 0
        nbh_count = 0

        for city_name, (city_profile, nbh_profiles) in all_cities.items():
            print(f"\n--- Inserting {city_name} ---")

            # City profile
            cp = upsert_city_profile(db, city_name, city_profile)
            city_count += 1
            print(f"  City profile: {cp.security_rating}")

            # Neighborhood profiles
            for nbh in nbh_profiles:
                nbh_name = nbh.get("name") or nbh.get("neighborhood")
                if not nbh_name:
                    continue
                np = upsert_neighborhood_profile(db, city_name, nbh_name, nbh)
                nbh_count += 1
                loc_str = f" (loc_id={np.location_id})" if np.location_id else " (no location link)"
                print(f"  {nbh_name}: {np.security_rating}{loc_str}")

        db.commit()
        print(f"\n=== Done: {city_count} city profiles, {nbh_count} neighborhood profiles ===")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()