# ADR-001: Multi-layer data model (raw/canonical/history) over single-table

**Status**: Accepted
**Date**: 2026-06-20

## Context

The original CentralImmo used a single `annonces` table that conflated listing (one source's offer) with property (the real-world building). When the same property appeared on Mapiole and Kasastay, it was stored as two rows. The `meilleur_prix` (best price) field was overwritten on each scrape (`fusion.py:97`), destroying price history. Raw original data (full description, original payload) was not preserved — descriptions were truncated to 100 chars.

## Decision

Adopt a 4-layer data model:

1. **`raw_listings`** — immutable original scraped data (one row per unique source URL). Idempotent on `url_hash = sha256(url_source)`. Re-crawls never update; they become `listing_history` events. Full payload stored in JSONB.
2. **`canonical_properties`** — a real-world property. Many `raw_listings` (from different sites) point to one canonical via `canonical_property_id` FK.
3. **`listing_history`** — append-only event log (`first_seen`, `price_change`, `availability_change`, `removed`). Never overwritten.
4. **`locations`** — normalized city/neighborhood reference. `raw_listings.location_raw` preserves the verbatim string; `canonical_properties.location_id` points to the resolved row.

## Rationale

- **Price history preservation**: append-only `listing_history` fixes the overwrite bug. Users can see a property's price evolution over time.
- **Raw data integrity**: `raw_listings` stores the full scraper output (description, payload, original image URLs) for audit and re-extraction.
- **Cross-source dedup**: multiple raw listings from different sites link to one canonical property, enabling "compare offers" in the UI.
- **Analytics grouping**: `GROUP BY location_id` on canonical_properties is far more efficient than re-parsing location strings per query.

## Consequences

- More tables (4 vs 1) but clearer separation of concerns.
- Migrations required to backfill from legacy `annonces`/`sources_annonces` (handled by Alembic 0001).
- Pre-migration price history is unrecoverable (accepted data loss — documented).