"""Add the nyetapiole source to the sources table.

Nyetapiole (nyetapiole.com) is a Cameroonian proptech that connects
property owners and tenants directly. It exposes a clean JSON API at
/api/v1/listing/articles (list) and /api/v1/listing/article/{slug}
(detail), both returning the same schema. A dedicated adapter
(scrapers/nyetapiole.py::NyetapioleAdapter) consumes the list endpoint
and normalizes listings to RawListingDraft.

Revision ID: 0007_nyetapiole
Revises: 0006_payments
Create Date: 2026-07-16
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0007_nyetapiole"
down_revision = "0006_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text(
        "INSERT INTO sources (slug, display_name, site_url, adapter_kind, is_active) "
        "VALUES (:slug, :name, :url, :kind, true) "
        "ON CONFLICT (slug) DO NOTHING"
    ), {
        "slug": "nyetapiole",
        "name": "Nyetapiole",
        "url": "https://nyetapiole.com",
        "kind": "dedicated",
    })


def downgrade() -> None:
    bind = op.get_bind()
    # Only remove the source row; raw_listings and canonical_properties
    # remain untouched (they reference source_id via FK, which will dangle
    # if the source is deleted — so we leave the row in downgrade to avoid
    # orphaning data. If a full rollback is needed, delete manually.)
    bind.execute(sa.text(
        "DELETE FROM sources WHERE slug = 'nyetapiole'"
    ))