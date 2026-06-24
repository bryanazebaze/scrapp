# ADR-002: Append-only event log over periodic snapshots for history

**Status**: Accepted
**Date**: 2026-06-20

## Context

The old system stored `meilleur_prix` as a single column on `annonces` and overwrote it on each crawl (`fusion.py:97`). Price changes were lost — there was no way to know what a property cost last month.

Two options were considered:
1. **Periodic snapshots**: store a full row per crawl (price, availability, etc.) in a `listing_snapshots` table. Every crawl creates a row.
2. **Append-only event log**: store only change events (`first_seen`, `price_change`, `availability_change`, `removed`). A row is created only when something actually changes.

## Decision

Use an **append-only event log** (`listing_history` table). The ingest pipeline compares each fresh scrape to the latest event for that `raw_listing_id` and appends a new event only if price or availability changed.

## Rationale

- **Storage efficiency**: price/availability rarely change. Most re-crawls are no-ops. A snapshot table would be 99%+ duplicate rows.
- **Meaningful events**: an event row represents a real market signal (price dropped, property disappeared). A snapshot row represents "we checked and nothing changed" — noise.
- **Demand score**: days-on-market is computed from the time between `first_seen` and `removed` events. This is impossible with overwrites and wasteful with snapshots.
- **Trend computation**: 90-day price trends compare `first_seen` prices between time windows — clean with events, noisy with snapshots.

## Consequences

- Pre-migration price history is unrecoverable (the old system didn't track it). Accepted.
- The scheduler's 6h refresh job compares to the latest event; no-op re-crawls are free (just a comparison, no row written).
- Reconstructing a property's full state at a point in time requires replaying events — but this is only needed for analytics, not user-facing display.