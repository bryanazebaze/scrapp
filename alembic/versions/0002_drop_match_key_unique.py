"""Drop the unique constraint on canonical_properties.match_key and switch
it to a plain index, then recompute all existing match_keys with the new
coarse formula (type + city + neighborhood, no title, no price).

Rationale: the 0001 migration created match_key as UNIQUE and computed it
with the title and a price bucket baked in. That was too strict — the same
property advertised on two sites with slightly different titles produced two
different keys and was never merged (verified end-to-end during Phase 3
testing). match_key is now a CANDIDATE-RETRIEVAL bucket, not a unique
identifier; multiple distinct properties in the same type+city+neighborhood
share a key and the DCS disambiguates them.

The recompute reads each canonical's resolved location (via location_id ->
locations) so the new key matches what the runtime matcher produces. If a
canonical has no location_id, its key is set to a per-row 'noloc:' hash so it
remains distinct (mirroring create_canonical's fallback in core.ingest).

Revision ID: 0002_drop_match_key_unique
Revises: 0001_initial
Create Date: 2026-06-20
"""
from __future__ import annotations

import hashlib
import unicodedata
import re

import sqlalchemy as sa
from alembic import op


revision = "0002_drop_match_key_unique"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _normalize(text):
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def _slugify(text):
    n = _normalize(text)
    n = re.sub(r"[^a-z0-9]+", "-", n)
    return n.strip("-")


def _new_key(prop_type, city, neighborhood, row_id):
    if not city:
        return f"noloc:{hashlib.sha1(str(row_id).encode()).hexdigest()[:32]}"
    parts = [
        _normalize(prop_type) or "unknown",
        _slugify(city) or "unknown",
        _slugify(neighborhood) or "unknown",
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


def upgrade() -> None:
    # 1. Drop the unique constraint; keep a plain (non-unique) index.
    op.drop_constraint("uq_canonical_match_key", "canonical_properties",
                       type_="unique")
    op.drop_index("idx_canonical_match_key", table_name="canonical_properties")
    op.create_index("idx_canonical_match_key", "canonical_properties",
                    ["match_key"], unique=False)

    # 2. Recompute every existing canonical's match_key with the new formula.
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT cp.id, cp.property_type, l.city, l.neighborhood "
        "FROM canonical_properties cp LEFT JOIN locations l ON cp.location_id = l.id"
    )).fetchall()
    for cid, ptype, city, neighborhood in rows:
        new_key = _new_key(ptype, city, neighborhood, cid)
        bind.execute(sa.text(
            "UPDATE canonical_properties SET match_key = :k WHERE id = :id"
        ), {"k": new_key, "id": cid})


def downgrade() -> None:
    # Restoring the old (incorrect) unique constraint is not safe because
    # multiple rows may now legitimately share a match_key. We leave the
    # plain index in place on downgrade.
    op.drop_index("idx_canonical_match_key", table_name="canonical_properties")
    op.create_index("idx_canonical_match_key", "canonical_properties",
                    ["match_key"], unique=True)
    op.create_unique_constraint("uq_canonical_match_key", "canonical_properties",
                                ["match_key"])