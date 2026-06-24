# ADR-003: Normalized locations table over denormalized strings

**Status**: Accepted
**Date**: 2026-06-20

## Context

The old system stored location as a free-text string (`localisation_brute` on `annonces`) and re-parsed it on every query. The `main_api.py` price-comparison endpoint (lines 67-76) hardcoded a city list and did `ilike` string matching per request. Analytics required re-parsing strings for `GROUP BY city`.

## Decision

Create a `locations` table with `city`, `neighborhood` (nullable), `district`, `lat`, `lng`, `slug`. The `slug` is a URL-safe identifier (`douala-bastos`). `raw_listings.location_raw` preserves the verbatim original string for audit; `canonical_properties.location_id` points to the resolved row.

`UNIQUE(city, COALESCE(neighborhood, ''))` prevents duplicate location rows.

## Rationale

- **Query efficiency**: `GROUP BY location_id` is an indexed integer join, not a string-parse-and-match per row.
- **Analytics**: neighborhood scores require grouping by location. A reference table makes this trivial.
- **Map support**: `lat`/`lng` on locations enables the Flutter map screen to place markers without geocoding each listing.
- **Slug-based URLs**: `/neighborhoods/douala-bastos` is clean and shareable.
- **Original string preserved**: `location_raw` on `raw_listings` keeps the verbatim text for display ("Bastos, Douala, Cameroun") even after normalization.

## Consequences

- New listings go through `resolve_location()` which parses `location_raw` into city/neighborhood and either finds or creates a location row.
- The migration backfills `location_id` as nullable; a post-migration geocoding pass can resolve coordinates.
- The Cameroon city/neighborhood dictionary in `scrapers/utils.py` (`CAMEROON_CITIES`, `CAMEROON_NEIGHBORHOODS`) drives the parsing. Unknown locations get a row with `neighborhood=None` so they still group correctly by city.