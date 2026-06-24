"""Add city_profiles and neighborhood_profiles tables.

Two new tables for security and geopolitical intelligence:

1. city_profiles — one row per city with security rating, threat landscape,
   safest zones, emergency contacts, curfew info, and general city description.

2. neighborhood_profiles — one row per (city, neighborhood) with security
   notes, amenities, transport info, real-estate context, demographics,
   landmarks, and risk factors. Optionally links to locations via FK.

Revision ID: 0004_add_profiles
Revises: 0003_data_quality_fixes
Create Date: 2026-06-23
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision = "0004_add_profiles"
down_revision = "0003_data_quality_fixes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- city_profiles ---
    op.create_table(
        "city_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("city", sa.String(80), nullable=False, unique=True),
        sa.Column("region", sa.String(80), nullable=True),
        sa.Column("security_rating", sa.String(20), nullable=True),
        sa.Column("security_summary", sa.Text(), nullable=True),
        sa.Column("current_threats", JSONB, nullable=True),
        sa.Column("safest_zones", JSONB, nullable=True),
        sa.Column("emergency_contacts", JSONB, nullable=True),
        sa.Column("travel_tips", sa.Text(), nullable=True),
        sa.Column("curfew_info", sa.Text(), nullable=True),
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column("area_description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_city_profiles_city", "city_profiles", ["city"])

    # --- neighborhood_profiles ---
    op.create_table(
        "neighborhood_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("location_id", sa.BigInteger(),
                   sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("neighborhood", sa.String(120), nullable=True),
        sa.Column("security_rating", sa.String(20), nullable=True),
        sa.Column("security_notes", sa.Text(), nullable=True),
        sa.Column("amenities", JSONB, nullable=True),
        sa.Column("transport_info", sa.Text(), nullable=True),
        sa.Column("real_estate_context", sa.Text(), nullable=True),
        sa.Column("demographics", sa.Text(), nullable=True),
        sa.Column("landmarks", JSONB, nullable=True),
        sa.Column("risk_factors", JSONB, nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_neighborhood_profiles_city", "neighborhood_profiles", ["city"]
    )
    op.create_index(
        "idx_neighborhood_profiles_location", "neighborhood_profiles", ["location_id"]
    )
    op.create_unique_constraint(
        "uq_neighborhood_profile_city_neighborhood",
        "neighborhood_profiles",
        ["city", "neighborhood"],
    )


def downgrade() -> None:
    op.drop_table("neighborhood_profiles")
    op.drop_table("city_profiles")