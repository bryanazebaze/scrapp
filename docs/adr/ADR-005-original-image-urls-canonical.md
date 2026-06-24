# ADR-005: Original image URLs as canonical record, filesystem as cache

**Status**: Accepted
**Date**: 2026-06-20

## Context

The old system's `est_annonce_valide()` (`fusion.py:32`) rejected listings whose `urls_images` didn't start with `/static/` — i.e., listings whose images hadn't been downloaded yet. This coupled validation to the cache state: a valid listing could be rejected just because its images weren't cached yet. The image download also mutated the `urls_images` field, replacing original URLs with local paths.

## Decision

- **`raw_listings.images_raw`** (JSONB) stores the **original image URLs** as the canonical record. This is never overwritten.
- **`image_cache`** table (optional) tracks local downloads: `url_hash` (PK), `original_url`, `local_path`, `bytes`, `source_id`. This is a cache — it can be cleared and rebuilt.
- The API serves both: `images_raw` for the canonical URLs, and the `/static/images/` mount for cached downloads.
- **Validation is decoupled from caching**: a listing is valid based on its data fields, not on whether images are cached.

## Rationale

- **No data loss**: original URLs are the source of truth. If the cache is cleared, images can be re-downloaded.
- **No validation coupling**: a listing with original URLs but no cache is still valid. The Flutter app can load images directly from the original URL (via `cached_network_image`) or from the cache.
- **Audit trail**: `images_raw` preserves what was actually on the source site, useful for re-extraction or dispute resolution.

## Consequences

- The scraper's `cache_images()` returns local paths but the original URLs are stored in `images_raw` regardless.
- The Flutter `CachedNetworkImage` widget handles loading from URLs transparently with its own in-memory + file cache.
- The `image_cache` table is populated lazily; it's not required for the app to function.