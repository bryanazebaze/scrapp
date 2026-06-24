"""Data-quality fixes: correct listing_history.availability, add CHECK
constraint, and backfill locations.lat/lng for known Cameroon neighborhoods.

Three fixes bundled in one migration (all are data corrections + one DDL
constraint addition):

1. listing_history.availability: the ingest pipeline's mark_removed() was
   setting availability='removed' on removed events. 'removed' is not a valid
   availability enum (the allowed set is available|unavailable|sold|rented,
   plus NULL). Fix the existing 220 bad rows by setting them to NULL (the
   event_type='removed' already conveys the semantics) and add a CHECK
   constraint to prevent recurrence.

2. locations.lat/lng: every location row has NULL coordinates because no
   geocoder was ever wired in. Backfill approximate centroids for the known
   Douala/Yaounde neighborhoods so the map view and analytics work. Future
   locations get coords at creation time via resolve_location().

3. canonical_properties.area_sqm: rows with area_sqm=0 are extraction
   failures, not real values. Set them to NULL so they don't poison the
   match_key (0 was collapsing distinct properties into one bucket).

Revision ID: 0003_data_quality_fixes
Revises: 0002_drop_match_key_unique
Create Date: 2026-06-23
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_data_quality_fixes"
down_revision = "0002_drop_match_key_unique"
branch_labels = None
depends_on = None


# Approximate centroids for known neighborhoods (lat, lng).
# Mirrors scrapers/utils.py:_NEIGHBORHOODS — kept inline so the migration is
# self-contained and doesn't import application code.
_NEIGHBORHOOD_COORDS: list[tuple[str, str, float, float]] = [
    # Douala
    ("Akwa", "Douala", 4.0597, 9.7036),
    ("Bonanjo", "Douala", 4.0463, 9.6981),
    ("Bonapriso", "Douala", 4.0389, 9.7047),
    ("Bonamoussadi", "Douala", 4.0500, 9.7333),
    ("Deido", "Douala", 4.0653, 9.7131),
    ("Kotto", "Douala", 4.0431, 9.7189),
    ("Makepe", "Douala", 4.0500, 9.7500),
    ("Logbessou", "Douala", 4.0833, 9.7000),
    ("Nkoulouloun", "Douala", 4.0667, 9.7167),
    ("Bonabéri", "Douala", 4.0750, 9.6833),
    ("New Bell", "Douala", 4.0333, 9.7167),
    ("Bali", "Douala", 4.0583, 9.6917),
    ("Mboppi", "Douala", 4.0417, 9.7083),
    ("Bassa", "Douala", 4.0500, 9.7000),
    ("Nylon", "Douala", 4.0333, 9.7333),
    ("Dakar", "Douala", 4.0333, 9.7000),
    ("Bercy", "Douala", 4.0167, 9.7333),
    ("Yassa", "Douala", 3.9833, 9.8000),
    ("Ndokoti", "Douala", 4.0333, 9.7500),
    # Yaoundé
    ("Bastos", "Yaoundé", 3.8833, 11.5167),
    ("Mvog-Mbi", "Yaoundé", 3.8500, 11.5000),
    ("Mendong", "Yaoundé", 3.8333, 11.4833),
    ("Odza", "Yaoundé", 3.8167, 11.5333),
    ("Mfandena", "Yaoundé", 3.8833, 11.5000),
    ("Emana", "Yaoundé", 3.8667, 11.4667),
    ("Ngoa-Ekelle", "Yaoundé", 3.8633, 11.5133),
    ("Bruxelles", "Yaoundé", 3.8667, 11.5000),
    ("Madagascar", "Yaoundé", 3.8667, 11.5167),
    ("Cité Verte", "Yaoundé", 3.8667, 11.5050),
    ("Simbock", "Yaoundé", 3.8333, 11.5333),
    ("Nsam", "Yaoundé", 3.8667, 11.5167),
    ("Nkolbisson", "Yaoundé", 3.8833, 11.4500),
    ("Biyem Assi", "Yaoundé", 3.8500, 11.4833),
    ("Ngombé", "Yaoundé", 3.8500, 11.5000),
    ("Mokolo", "Yaoundé", 3.8667, 11.5000),
    ("Elig-Edzoa", "Yaoundé", 3.8667, 11.5167),
    ("Etoudi", "Yaoundé", 3.9000, 11.5167),
    ("Mvan", "Yaoundé", 3.8333, 11.5000),
    ("Mvog-Ada", "Yaoundé", 3.8500, 11.5167),
    ("Tsinga", "Yaoundé", 3.8833, 11.5167),
    ("Olembe", "Yaoundé", 3.9167, 11.5833),
    ("Ahala", "Yaoundé", 3.8500, 11.5500),
    ("Ngousso", "Yaoundé", 3.8500, 11.5167),
    ("Odja", "Yaoundé", 3.8333, 11.5167),
]


def upgrade() -> None:
    bind = op.get_bind()

    # 1a. Fix existing listing_history rows with the invalid 'removed' value.
    bind.execute(sa.text(
        "UPDATE listing_history SET availability = NULL "
        "WHERE availability = 'removed'"
    ))

    # 1b. Add CHECK constraint to prevent recurrence.
    op.create_check_constraint(
        "ck_listing_history_availability",
        "listing_history",
        "availability IS NULL OR availability IN "
        "('available', 'unavailable', 'sold', 'rented')",
    )

    # 2. Backfill locations.lat/lng for known neighborhoods.
    for neighborhood, city, lat, lng in _NEIGHBORHOOD_COORDS:
        bind.execute(sa.text(
            "UPDATE locations SET lat = :lat, lng = :lng "
            "WHERE LOWER(city) = LOWER(:city) "
            "AND COALESCE(LOWER(neighborhood), '') = LOWER(:nb) "
            "AND (lat IS NULL OR lng IS NULL)"
        ), {"lat": lat, "lng": lng, "city": city, "nb": neighborhood})

    # 3. Fix canonical_properties.area_sqm = 0 (extraction failures).
    bind.execute(sa.text(
        "UPDATE canonical_properties SET area_sqm = NULL "
        "WHERE area_sqm IS NOT NULL AND area_sqm <= 0"
    ))


def downgrade() -> None:
    op.drop_constraint("ck_listing_history_availability", "listing_history",
                       type_="check")
    # The data corrections (availability NULL, lat/lng backfill, area_sqm NULL)
    # are not reversible — we cannot recover the original invalid values.