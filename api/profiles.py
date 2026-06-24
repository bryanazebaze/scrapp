"""Security & intelligence profile endpoints.

Exposes city_profiles and neighborhood_profiles for the Flutter app to
display safety, amenity, and real-estate context alongside listings.

Bilingual: serves French (stored) by default, English when the
Accept-Language header requests it. English values come from the *_en
mirror columns populated by scripts/translate_profiles_to_english.py;
NULL English values fall back to the French column.

Endpoints:
  GET /profiles/cities                        — list all city profiles
  GET /profiles/cities/{city}                 — one city profile
  GET /profiles/neighborhoods                 — list all neighborhood profiles (filter by city)
  GET /profiles/neighborhoods/{id}            — one neighborhood profile by ID
  GET /profiles/neighborhoods/by-location/{location_id}  — neighborhood profile by location
  GET /profiles/city/{city}/neighborhoods     — all neighborhood profiles in a city
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.i18n import pick, preferred_lang, rating_for_lang
from core.models import CityProfile, NeighborhoodProfile, Location
from core.schemas import CityProfileSchema, NeighborhoodProfileSchema

router = APIRouter(prefix="/profiles", tags=["profiles"])


# --------------------------------------------------------------------------- #
# Localization helpers — build a flat dict matching the Pydantic schema,
# picking the *_en column when lang == "en" (falling back to French).
# --------------------------------------------------------------------------- #
def localize_city(row: CityProfile, lang: str) -> dict:
    if lang == "en":
        return {
            "id": row.id,
            "city": row.city,
            "region": row.region,
            "security_rating": rating_for_lang(row.security_rating, lang),
            "security_summary": pick(row.security_summary_en, row.security_summary),
            "current_threats": pick(row.current_threats_en, row.current_threats),
            "safest_zones": pick(row.safest_zones_en, row.safest_zones),
            "emergency_contacts": pick(row.emergency_contacts_en, row.emergency_contacts),
            "travel_tips": pick(row.travel_tips_en, row.travel_tips),
            "curfew_info": pick(row.curfew_info_en, row.curfew_info),
            "population": row.population,
            "area_description": pick(row.area_description_en, row.area_description),
        }
    return {
        "id": row.id,
        "city": row.city,
        "region": row.region,
        "security_rating": row.security_rating,
        "security_summary": row.security_summary,
        "current_threats": row.current_threats,
        "safest_zones": row.safest_zones,
        "emergency_contacts": row.emergency_contacts,
        "travel_tips": row.travel_tips,
        "curfew_info": row.curfew_info,
        "population": row.population,
        "area_description": row.area_description,
    }


def localize_neighborhood(row: NeighborhoodProfile, lang: str) -> dict:
    if lang == "en":
        return {
            "id": row.id,
            "location_id": row.location_id,
            "city": row.city,
            "neighborhood": row.neighborhood,
            "security_rating": rating_for_lang(row.security_rating, lang),
            "security_notes": pick(row.security_notes_en, row.security_notes),
            "amenities": pick(row.amenities_en, row.amenities),
            "transport_info": pick(row.transport_info_en, row.transport_info),
            "real_estate_context": pick(row.real_estate_context_en, row.real_estate_context),
            "demographics": pick(row.demographics_en, row.demographics),
            "landmarks": pick(row.landmarks_en, row.landmarks),
            "risk_factors": pick(row.risk_factors_en, row.risk_factors),
            "description": pick(row.description_en, row.description),
        }
    return {
        "id": row.id,
        "location_id": row.location_id,
        "city": row.city,
        "neighborhood": row.neighborhood,
        "security_rating": row.security_rating,
        "security_notes": row.security_notes,
        "amenities": row.amenities,
        "transport_info": row.transport_info,
        "real_estate_context": row.real_estate_context,
        "demographics": row.demographics,
        "landmarks": row.landmarks,
        "risk_factors": row.risk_factors,
        "description": row.description,
    }


# --------------------------------------------------------------------------- #
# City profiles
# --------------------------------------------------------------------------- #
@router.get("/cities", response_model=List[CityProfileSchema])
def list_city_profiles(request: Request, db: Session = Depends(get_db)):
    """List all city security profiles."""
    lang = preferred_lang(request)
    rows = db.query(CityProfile).order_by(CityProfile.city).all()
    return [localize_city(r, lang) for r in rows]


@router.get("/cities/{city}", response_model=CityProfileSchema)
def get_city_profile(city: str, request: Request, db: Session = Depends(get_db)):
    """Get the security profile for one city."""
    profile = db.query(CityProfile).filter(CityProfile.city == city).first()
    if not profile:
        raise HTTPException(404, f"No profile found for city '{city}'")
    return localize_city(profile, preferred_lang(request))


# --------------------------------------------------------------------------- #
# Neighborhood profiles
# --------------------------------------------------------------------------- #
@router.get("/neighborhoods", response_model=List[NeighborhoodProfileSchema])
def list_neighborhood_profiles(
    request: Request,
    city: Optional[str] = Query(None, help="Filter by city name"),
    db: Session = Depends(get_db),
):
    """List neighborhood profiles, optionally filtered by city."""
    lang = preferred_lang(request)
    q = db.query(NeighborhoodProfile)
    if city:
        q = q.filter(NeighborhoodProfile.city == city)
    rows = q.order_by(NeighborhoodProfile.city, NeighborhoodProfile.neighborhood).all()
    return [localize_neighborhood(r, lang) for r in rows]


@router.get("/neighborhoods/{profile_id}", response_model=NeighborhoodProfileSchema)
def get_neighborhood_profile(profile_id: int, request: Request, db: Session = Depends(get_db)):
    """Get one neighborhood profile by its ID."""
    profile = db.query(NeighborhoodProfile).filter(
        NeighborhoodProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(404, f"Neighborhood profile #{profile_id} not found")
    return localize_neighborhood(profile, preferred_lang(request))


@router.get("/neighborhoods/by-location/{location_id}",
             response_model=NeighborhoodProfileSchema)
def get_profile_by_location(location_id: int, request: Request, db: Session = Depends(get_db)):
    """Get the neighborhood profile linked to a location (by location_id)."""
    profile = db.query(NeighborhoodProfile).filter(
        NeighborhoodProfile.location_id == location_id
    ).first()
    if not profile:
        # Try to find by matching city + neighborhood on the location
        loc = db.query(Location).filter(Location.id == location_id).first()
        if not loc:
            raise HTTPException(404, f"Location #{location_id} not found")
        q = db.query(NeighborhoodProfile).filter(
            NeighborhoodProfile.city == loc.city
        )
        if loc.neighborhood:
            q = q.filter(NeighborhoodProfile.neighborhood == loc.neighborhood)
        else:
            q = q.filter(NeighborhoodProfile.neighborhood.is_(None))
        profile = q.first()
        if not profile:
            raise HTTPException(404, "No profile linked to this location")
    return localize_neighborhood(profile, preferred_lang(request))


@router.get("/city/{city}/neighborhoods",
             response_model=List[NeighborhoodProfileSchema])
def get_city_neighborhood_profiles(city: str, request: Request, db: Session = Depends(get_db)):
    """All neighborhood profiles within a city."""
    lang = preferred_lang(request)
    profiles = db.query(NeighborhoodProfile).filter(
        NeighborhoodProfile.city == city
    ).order_by(NeighborhoodProfile.neighborhood).all()
    if not profiles:
        raise HTTPException(404, f"No neighborhood profiles found for '{city}'")
    return [localize_neighborhood(p, lang) for p in profiles]


@router.get("/city/{city}/full")
def get_city_full_profile(city: str, request: Request, db: Session = Depends(get_db)):
    """Combined endpoint: city profile + all neighborhood profiles in one call.

    Useful for the Flutter app to render a full city safety page in one request.
    """
    lang = preferred_lang(request)
    city_prof = db.query(CityProfile).filter(CityProfile.city == city).first()
    nbh_profs = db.query(NeighborhoodProfile).filter(
        NeighborhoodProfile.city == city
    ).order_by(NeighborhoodProfile.neighborhood).all()

    if not city_prof and not nbh_profs:
        raise HTTPException(404, f"No profiles found for city '{city}'")

    return {
        "city": CityProfileSchema.model_validate(localize_city(city_prof, lang)) if city_prof else None,
        "neighborhoods": [
            NeighborhoodProfileSchema.model_validate(localize_neighborhood(np, lang))
            for np in nbh_profs
        ],
    }