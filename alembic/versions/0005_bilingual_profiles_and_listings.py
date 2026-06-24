"""Add bilingual *_en columns to profiles and a listing_translations table.

The Flutter app's language toggle previously had no effect on DB-fetched
content because profiles and listing descriptions were stored in a single
language. The French translation script destructively overwrote the original
English profile text; listing descriptions are natively French (scraped from
Mapiole). This migration adds English-mirror columns so both languages can
coexist, and introduces a separate listing_translations table (raw_listings
is immutable per project conventions, so translations live alongside, not on,
the raw row).

Revision ID: 0005_bilingual
Revises: 0004_add_profiles
Create Date: 2026-06-24
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision = "0005_bilingual"
down_revision = "0004_add_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- city_profiles: English mirrors ---
    op.add_column("city_profiles",
                  sa.Column("security_summary_en", sa.Text(), nullable=True))
    op.add_column("city_profiles",
                  sa.Column("travel_tips_en", sa.Text(), nullable=True))
    op.add_column("city_profiles",
                  sa.Column("curfew_info_en", sa.Text(), nullable=True))
    op.add_column("city_profiles",
                  sa.Column("area_description_en", sa.Text(), nullable=True))
    op.add_column("city_profiles",
                  sa.Column("current_threats_en", JSONB, nullable=True))
    op.add_column("city_profiles",
                  sa.Column("safest_zones_en", JSONB, nullable=True))
    op.add_column("city_profiles",
                  sa.Column("emergency_contacts_en", JSONB, nullable=True))

    # --- neighborhood_profiles: English mirrors ---
    op.add_column("neighborhood_profiles",
                  sa.Column("security_notes_en", sa.Text(), nullable=True))
    op.add_column("neighborhood_profiles",
                  sa.Column("transport_info_en", sa.Text(), nullable=True))
    op.add_column("neighborhood_profiles",
                  sa.Column("real_estate_context_en", sa.Text(), nullable=True))
    op.add_column("neighborhood_profiles",
                  sa.Column("demographics_en", sa.Text(), nullable=True))
    op.add_column("neighborhood_profiles",
                  sa.Column("description_en", sa.Text(), nullable=True))
    op.add_column("neighborhood_profiles",
                  sa.Column("amenities_en", JSONB, nullable=True))
    op.add_column("neighborhood_profiles",
                  sa.Column("landmarks_en", JSONB, nullable=True))
    op.add_column("neighborhood_profiles",
                  sa.Column("risk_factors_en", JSONB, nullable=True))

    # --- listing_translations: respects raw_listings immutability ---
    op.create_table(
        "listing_translations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("raw_listing_id", sa.BigInteger(),
                  sa.ForeignKey("raw_listings.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("language", sa.String(5), nullable=False),  # 'en' | 'fr'
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("raw_listing_id", "language",
                            name="uq_listing_translation_lang"),
    )
    op.create_index("idx_listing_translations_listing",
                    "listing_translations", ["raw_listing_id"])


def downgrade() -> None:
    op.drop_index("idx_listing_translations_listing", table_name="listing_translations")
    op.drop_table("listing_translations")

    for col in ("risk_factors_en", "landmarks_en", "amenities_en",
                "description_en", "demographics_en", "real_estate_context_en",
                "transport_info_en", "security_notes_en"):
        op.drop_column("neighborhood_profiles", col)

    for col in ("emergency_contacts_en", "safest_zones_en", "current_threats_en",
                "area_description_en", "curfew_info_en", "travel_tips_en",
                "security_summary_en"):
        op.drop_column("city_profiles", col)