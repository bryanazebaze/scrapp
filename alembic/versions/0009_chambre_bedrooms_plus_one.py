"""Backfill +1 bedroom for existing Chambre-type listings.

A listing with property_type='Chambre' is itself one room, so its bedroom
count must be incremented by 1 (mirrors the ingest-side rule added in
core/ingest.py: when property_type == 'Chambre', bedrooms = (bedrooms or 0) + 1).

This migration is a one-shot data fix for canonical_properties rows crawled
before that rule existed. It only touches rows where property_type='Chambre'.
New rows go through core/ingest.create_canonical which already applies the +1.

Idempotency: alembic_version prevents re-running. Do NOT re-apply manually
or rows will be double-incremented.
"""
from alembic import op


revision = "0009_chambre_bedrooms_plus_one"
down_revision = "0008_auth_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE canonical_properties
        SET bedrooms = COALESCE(bedrooms, 0) + 1
        WHERE property_type = 'Chambre'
        """
    )


def downgrade() -> None:
    # Reversing the +1 on potentially-null bedrooms is ambiguous and unsafe
    # (we cannot distinguish pre-backfill from post-backfill values). No-op.
    pass