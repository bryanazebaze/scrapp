# ADR-006: Confidence-scored universal scraper with human review gate

**Status**: Accepted
**Date**: 2026-06-20

## Context

Dedicated scrapers (Mapiole, Kasastay) are hand-written for specific sites and produce high-quality data. But the real-estate market has many small sites, and writing a dedicated adapter for each is impractical. We needed a way to onboard a new site in minutes, before a dedicated scraper is written.

## Decision

Build a **universal fallback scraper** (`scrapers/universal.py`) that:
1. Discovers listing pages (sitemap.xml + link patterns + pagination).
2. Detects property cards heuristically (repeated DOM structures with 3-of-5 signals: image, link, price text, city keyword, repeated signature).
3. Extracts fields via ordered strategies: JSON-LD → OpenGraph → heuristic DOM.
4. Computes a **confidence score** (0.0–1.0) from 6 factors: schema presence, card structure, price validity, image resolvability, location detection, domain allowlist.

**Gating thresholds**:
- `≥ 0.75` → `auto_promoted` (canonical property created/linked automatically)
- `0.40–0.74` → `pending` (raw_listing stored with `canonical_property_id=NULL`, awaiting human review)
- `< 0.40` → `rejected` at ingest (not stored)

**Human review flow**: admin approves via `POST /admin/review/{id}` → match resolution runs → canonical created/linked → `first_seen` event backdated to `crawled_at` (preserving the property's age).

## Rationale

- **Fast onboarding**: point the universal scraper at a new URL and it produces drafts immediately. Low-confidence ones sit in the review queue.
- **Quality control**: the confidence score separates "this looks like a real listing" (JSON-LD + price + images) from "this is noise" (heuristic-only with no price).
- **No orphan canonicals**: pending listings do NOT create canonical properties. Only `auto_promoted` or human-approved listings create/link canonicals. This prevents garbage canonicals from polluting search results.
- **Explainability**: the `match_explanation` JSONB stores which extraction strategy supplied each field, so the reviewer can see why confidence is what it is.

## Consequences

- The admin review UI (`/admin/review/pending`) is needed for universal-scraper sources to be useful.
- Low-quality sites produce mostly pending/rejected listings — acceptable, they don't pollute the canonical set.
- The confidence formula is tunable (weights in `confidence.py`); thresholds can be adjusted per source via `crawl_config`.