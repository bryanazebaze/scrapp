"""Initial multi-layer schema + backfill from legacy annonces/sources_annonces.

Creates: sources, locations, raw_listings, canonical_properties, listing_history,
image_cache, scheduler_jobs, neighborhood_analytics.

If the legacy tables annonces / sources_annonces already exist (created by the
previous Base.metadata.create_all flow), this migration backfills them into the
new layer model and renames them to annonces_legacy / sources_annonces_legacy so
the data is preserved but out of the way. Pre-migration price-change history is
not recoverable and is accepted as data loss (documented in ADR-002).

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-20
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


# --------------------------------------------------------------------------- #
# Migration helpers (self-contained — do NOT import from core.* so the
# migration stays frozen and reproducible regardless of later refactors).
# --------------------------------------------------------------------------- #
def _normalize(text: str | None) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def _slugify(text: str | None) -> str:
    n = _normalize(text)
    n = re.sub(r"[^a-z0-9]+", "-", n)
    return n.strip("-")


def _price_bucket(price) -> int | None:
    if price is None:
        return None
    try:
        p = int(price)
    except (TypeError, ValueError):
        return None
    bucket_size = 50000
    return (p // bucket_size) * bucket_size


def _match_key(prop_type: str | None, city: str | None,
               neighborhood: str | None, price, title: str | None) -> str:
    parts = [
        _normalize(prop_type) or "unknown",
        _slugify(city) or "unknown",
        _slugify(neighborhood) or "unknown",
        str(_price_bucket(price) or "0"),
        _normalize(title),
    ]
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


# Known Cameroon cities (mirrors the inline list previously in main_api.py).
_CITIES = [
    "Douala", "Yaoundé", "Bafoussam", "Garoua", "Maroua", "Bamenda",
    "Ngaoundéré", "Bertoua", "Ebolowa", "Kribi", "Limbe", "Buea",
    "Nkongsamba", "Edéa", "Kumba", "Bastos", "Akwa", "Bonanjo", "Kotto",
    "Bonapriso", "Simbock",
]


def _detect_city(location: str | None) -> tuple[str | None, str | None]:
    """Return (city, neighborhood) parsed from a raw location string."""
    if not location:
        return None, None
    low = location.lower()
    city = None
    for c in _CITIES:
        if c.lower() in low:
            city = c
            break
    # Neighborhood heuristic: text before a comma/separator, or a known
    # neighborhood token. Conservative: only flag if it differs from the city.
    neighborhood = None
    for sep in [",", " - ", "–", "/"]:
        if sep in location:
            head = location.split(sep)[0].strip()
            if head and head.lower() not in (city or "").lower():
                neighborhood = head
            break
    return city, neighborhood


# --------------------------------------------------------------------------- #
# Table definitions (mirror core/models.py exactly so offline mode works too)
# --------------------------------------------------------------------------- #
def _create_tables() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(60), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("site_url", sa.String(500), nullable=False),
        sa.Column("adapter_kind", sa.String(30), nullable=False, server_default="dedicated"),
        sa.Column("robots_txt_url", sa.String(500)),
        sa.Column("crawl_config", postgresql.JSONB()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_sources_slug"),
    )
    op.create_index("idx_sources_slug", "sources", ["slug"], unique=True)

    op.create_table(
        "locations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("neighborhood", sa.String(120)),
        sa.Column("district", sa.String(80)),
        sa.Column("lat", sa.Float()),
        sa.Column("lng", sa.Float()),
        sa.Column("slug", sa.String(140), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("city", "neighborhood", name="uq_location_city_neighborhood"),
    )
    op.create_index("idx_location_slug", "locations", ["slug"], unique=True)
    op.create_index("idx_location_city", "locations", ["city"])

    op.create_table(
        "canonical_properties",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("match_key", sa.String(64), nullable=False),
        sa.Column("title_canonical", sa.Text(), nullable=False),
        sa.Column("title_normalized", sa.Text(), nullable=False),
        sa.Column("property_type", sa.String(30), nullable=False),
        sa.Column("location_id", sa.BigInteger(), sa.ForeignKey("locations.id")),
        sa.Column("bedrooms", sa.SmallInteger()),
        sa.Column("bathrooms", sa.SmallInteger()),
        sa.Column("area_sqm", sa.Float()),
        sa.Column("current_best_price", sa.BigInteger()),
        sa.Column("current_availability", sa.String(20), server_default="available"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("match_key", name="uq_canonical_match_key"),
    )
    op.create_index("idx_canonical_match_key", "canonical_properties", ["match_key"], unique=True)
    op.create_index("idx_canonical_location", "canonical_properties", ["location_id"])
    op.create_index("idx_canonical_type_loc", "canonical_properties", ["property_type", "location_id"])
    op.create_index("idx_canonical_property_type", "canonical_properties", ["property_type"])

    op.create_table(
        "raw_listings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("url_source", sa.Text(), nullable=False),
        sa.Column("url_hash", sa.String(64), nullable=False),
        sa.Column("title_raw", sa.Text(), nullable=False),
        sa.Column("price_raw", sa.Text()),
        sa.Column("price_parsed", sa.BigInteger()),
        sa.Column("currency", sa.String(10), server_default="XAF"),
        sa.Column("location_raw", sa.Text()),
        sa.Column("description_raw", sa.Text()),
        sa.Column("property_type_raw", sa.String(60)),
        sa.Column("images_raw", postgresql.JSONB()),
        sa.Column("payload", postgresql.JSONB()),
        sa.Column("crawl_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crawled_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("canonical_property_id", sa.BigInteger(), sa.ForeignKey("canonical_properties.id")),
        sa.Column("match_confidence", sa.Float()),
        sa.Column("match_explanation", postgresql.JSONB()),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        sa.UniqueConstraint("url_hash", name="uq_raw_url_hash"),
    )
    op.create_index("idx_raw_source_crawled", "raw_listings", ["source_id", "crawled_at"])
    op.create_index("idx_raw_canonical", "raw_listings", ["canonical_property_id"])
    op.create_index("idx_raw_review", "raw_listings", ["review_status"])
    op.create_index("idx_raw_source_id", "raw_listings", ["source_id"])

    op.create_table(
        "listing_history",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("raw_listing_id", sa.BigInteger(), sa.ForeignKey("raw_listings.id"), nullable=False),
        sa.Column("canonical_property_id", sa.BigInteger(), sa.ForeignKey("canonical_properties.id"), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("price_observed", sa.BigInteger()),
        sa.Column("availability", sa.String(20)),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("crawl_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("diff", postgresql.JSONB()),
    )
    op.create_index("idx_history_canon_time", "listing_history", ["canonical_property_id", "observed_at"])
    op.create_index("idx_history_raw", "listing_history", ["raw_listing_id"])
    op.create_index("idx_history_raw_latest", "listing_history", ["raw_listing_id", "observed_at"])

    op.create_table(
        "image_cache",
        sa.Column("url_hash", sa.String(64), primary_key=True),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("local_path", sa.Text(), nullable=False),
        sa.Column("bytes", sa.Integer()),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_image_cache_source", "image_cache", ["source_id"])

    op.create_table(
        "scheduler_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(40), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
        sa.Column("cron_expr", sa.String(60)),
        sa.Column("last_run", sa.DateTime(timezone=True)),
        sa.Column("next_run", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("last_error", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_scheduler_jobs_source", "scheduler_jobs", ["source_id"])

    op.create_table(
        "neighborhood_analytics",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("location_id", sa.BigInteger(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("property_type", sa.String(30)),
        sa.Column("period", sa.String(20), nullable=False, server_default="current"),
        sa.Column("listing_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_price", sa.BigInteger()),
        sa.Column("median_price", sa.BigInteger()),
        sa.Column("min_price", sa.BigInteger()),
        sa.Column("max_price", sa.BigInteger()),
        sa.Column("price_per_sqm", sa.Float()),
        sa.Column("premium_score", sa.Float()),
        sa.Column("demand_score", sa.Float()),
        sa.Column("growth_score", sa.Float()),
        sa.Column("activity_score", sa.Float()),
        sa.Column("luxury_score", sa.Float()),
        sa.Column("trend_direction", sa.String(10)),
        sa.Column("trend_pct", sa.Float()),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("location_id", "property_type", "period", name="uq_analytics_loc_type_period"),
    )
    op.create_index("idx_analytics_location", "neighborhood_analytics", ["location_id"])


def _drop_tables() -> None:
    for t in ["neighborhood_analytics", "scheduler_jobs", "image_cache",
              "listing_history", "raw_listings", "canonical_properties",
              "locations", "sources"]:
        op.drop_table_if_exists(t) if hasattr(op, "drop_table_if_exists") else op.drop_table(t)


# --------------------------------------------------------------------------- #
# Legacy backfill
# --------------------------------------------------------------------------- #
_SOURCES_SEED = [
    ("mapiole", "Mapiole", "https://mapiole.com", "dedicated"),
    ("kasastay", "Kasastay", "https://kasastay.com", "dedicated"),
]


def _backfill_from_legacy() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    has_legacy_annonces = inspector.has_table("annonces")
    has_legacy_sources = inspector.has_table("sources_annonces")

    # 1. Seed sources (always, even on a fresh DB).
    for slug, name, url, kind in _SOURCES_SEED:
        bind.execute(sa.text(
            "INSERT INTO sources (slug, display_name, site_url, adapter_kind, is_active) "
            "VALUES (:slug, :name, :url, :kind, true) "
            "ON CONFLICT (slug) DO NOTHING"
        ), {"slug": slug, "name": name, "url": url, "kind": kind})

    if not has_legacy_annonces or not has_legacy_sources:
        # Fresh DB — nothing to backfill.
        return

    session_id = uuid.uuid4()
    # Map legacy platform name -> new source id.
    rows = bind.execute(sa.text("SELECT id, slug FROM sources")).fetchall()
    source_by_name = {
        "Mapiole": next((r[0] for r in rows if r[1] == "mapiole"), None),
        "Kasastay": next((r[0] for r in rows if r[1] == "kasastay"), None),
        # Tolerate the older spelling used in some rows.
        "Kassataya": next((r[0] for r in rows if r[1] == "kasastay"), None),
    }

    legacy_annonces = bind.execute(sa.text(
        "SELECT id, titre, titre_normalise, type_de_bien, localisation_brute, "
        "description, urls_images, date_collecte, meilleur_prix FROM annonces"
    )).fetchall()

    # Cache for locations: (city, neighborhood) -> location_id
    loc_cache: dict[tuple[str | None, str | None], int] = {}

    def _get_or_create_location(city, neighborhood) -> int | None:
        if not city and not neighborhood:
            return None
        key = (city, neighborhood)
        if key in loc_cache:
            return loc_cache[key]
        slug = _slugify("-".join(filter(None, [city, neighborhood]))) or "unknown"
        bind.execute(sa.text(
            "INSERT INTO locations (city, neighborhood, slug) "
            "VALUES (:city, :nb, :slug) ON CONFLICT (city, neighborhood) DO NOTHING"
        ), {"city": city, "nb": neighborhood, "slug": slug})
        rid = bind.execute(sa.text(
            "SELECT id FROM locations WHERE city = :city "
            "AND COALESCE(neighborhood, '') = COALESCE(:nb, '')"
        ), {"city": city, "nb": neighborhood}).scalar()
        loc_cache[key] = rid
        return rid

    canon_id_by_legacy: dict[int, int] = {}

    for a_id, titre, titre_norm, type_bien, loc_brute, desc, urls_images, date_c, meilleur_prix in legacy_annonces:
        city, neighborhood = _detect_city(loc_brute)
        loc_id = _get_or_create_location(city, neighborhood)
        title_norm = titre_norm or _normalize(titre)
        mk = _match_key(type_bien, city, neighborhood, meilleur_prix, titre)

        # Insert canonical property (skip if match_key already present).
        existing_canon = bind.execute(sa.text(
            "SELECT id FROM canonical_properties WHERE match_key = :mk"
        ), {"mk": mk}).first()
        if existing_canon:
            canon_id = existing_canon[0]
        else:
            bind.execute(sa.text(
                "INSERT INTO canonical_properties "
                "(match_key, title_canonical, title_normalized, property_type, location_id, "
                " current_best_price, current_availability, created_at, last_seen_at, is_active) "
                "VALUES (:mk, :tc, :tn, :pt, :lid, :bp, 'available', :ts, :ts, true)"
            ), {
                "mk": mk, "tc": titre or "Untitled", "tn": title_norm,
                "pt": type_bien or "Inconnu", "lid": loc_id,
                "bp": meilleur_prix, "ts": date_c,
            })
            canon_id = bind.execute(sa.text(
                "SELECT id FROM canonical_properties WHERE match_key = :mk"
            ), {"mk": mk}).scalar()
        canon_id_by_legacy[a_id] = canon_id

        # Migrate the source rows for this legacy annonce.
        src_rows = bind.execute(sa.text(
            "SELECT id, nom_plateforme, url_source, prix_entier, date_collecte, particularite "
            "FROM sources_annonces WHERE annonce_id = :aid"
        ), {"aid": a_id}).fetchall()

        # Track best price across sources for the canonical row.
        best_price = None
        for _sid, nom_pl, url_src, prix, src_date, part in src_rows:
            src_id = source_by_name.get(nom_pl)
            if src_id is None:
                continue
            url_hash = hashlib.sha256((url_src or "").encode("utf-8")).hexdigest()
            images_list = []
            if urls_images:
                images_list = [u.strip() for u in urls_images.split(",") if u.strip()]
            payload = {
                "titre": titre, "type_de_bien": type_bien,
                "localisation_brute": loc_brute, "description": desc,
                "particularite": part, "legacy_annonce_id": a_id,
                "legacy_source_id": _sid,
            }
            bind.execute(sa.text(
                "INSERT INTO raw_listings "
                "(source_id, url_source, url_hash, title_raw, price_raw, price_parsed, "
                " currency, location_raw, description_raw, property_type_raw, images_raw, "
                " payload, crawl_session_id, crawled_at, canonical_property_id, "
                " match_confidence, review_status) "
                "VALUES (:sid, :us, :uh, :tr, :pr, :pp, 'XAF', :lr, :dr, :ptr, "
                "        CAST(:img AS jsonb), CAST(:pay AS jsonb), :cs, :ct, :cpid, 1.0, 'auto_promoted') "
                "ON CONFLICT (url_hash) DO NOTHING"
            ), {
                "sid": src_id, "us": url_src, "uh": url_hash,
                "tr": titre or "Untitled", "pr": str(prix) if prix is not None else None,
                "pp": prix, "lr": loc_brute, "dr": desc,
                "ptr": type_bien, "img": _json(images_list), "pay": _json(payload),
                "cs": session_id, "ct": src_date, "cpid": canon_id,
            })
            raw_id = bind.execute(sa.text(
                "SELECT id FROM raw_listings WHERE url_hash = :uh"
            ), {"uh": url_hash}).scalar()
            if raw_id is not None and canon_id is not None:
                bind.execute(sa.text(
                    "INSERT INTO listing_history "
                    "(raw_listing_id, canonical_property_id, event_type, price_observed, "
                    " availability, observed_at, crawl_session_id) "
                    "VALUES (:rid, :cid, 'first_seen', :pr, 'available', :ts, :cs)"
                ), {"rid": raw_id, "cid": canon_id, "pr": prix, "ts": src_date, "cs": session_id})
            if prix is not None and (best_price is None or prix < best_price):
                best_price = prix

        if best_price is not None and canon_id is not None:
            bind.execute(sa.text(
                "UPDATE canonical_properties SET current_best_price = :bp WHERE id = :cid"
            ), {"bp": best_price, "cid": canon_id})

    # Rename legacy tables out of the way (keep for safety; drop later).
    op.rename_table("annonces", "annonces_legacy")
    op.rename_table("sources_annonces", "sources_annonces_legacy")


def _json(value):
    """Wrap a Python value as a JSONB literal for the bind."""
    import json
    return json.dumps(value)


# --------------------------------------------------------------------------- #
# Migration entry points
# --------------------------------------------------------------------------- #
def upgrade() -> None:
    _create_tables()
    _backfill_from_legacy()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    # Restore legacy tables if they were renamed.
    if inspector.has_table("annonces_legacy"):
        op.rename_table("annonces_legacy", "annonces")
    if inspector.has_table("sources_annonces_legacy"):
        op.rename_table("sources_annonces_legacy", "sources_annonces")
    for t in ["neighborhood_analytics", "scheduler_jobs", "image_cache",
              "listing_history", "raw_listings", "canonical_properties",
              "locations", "sources"]:
        op.drop_table(t)