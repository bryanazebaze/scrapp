# ADR-004: match_key index lookup over ±15% price-range scan for dedup

**Status**: Accepted
**Date**: 2026-06-20

## Context

The old dedup logic (`fusion.py:56-59`) scanned the entire `annonces` table for listings within ±15% of the new listing's price, then ran rapidfuzz on the title. This is O(N) per insert — doesn't scale past a few thousand listings.

## Decision

Use a **coarse `match_key`** as a candidate-retrieval bucket: `sha1(property_type | city | neighborhood)`. This groups properties by type and location. Dedup becomes:

1. **O(1) index lookup**: query `canonical_properties WHERE match_key = ?` — returns all canonicals in the same type+location bucket.
2. **Composite DCS disambiguation**: for each candidate, compute the Duplicate Confidence Score (title similarity + price proximity + type + surface + bedrooms + location + image overlap). The best candidate is confirmed if DCS ≥ 0.85 or title_sim ≥ 80.

`match_key` is indexed but NOT unique — multiple distinct properties in the same bucket share a key and the DCS disambiguates.

## Rationale

- **Scalability**: O(1) index lookup replaces O(N) scan. 10K listings: ~10 candidates per bucket vs 10K full scan.
- **Cross-source matching**: the same property on Mapiole and Kasastay has slightly different titles but the same type+city+neighborhood → same match_key → found by the candidate query → DCS confirms.
- **Coarse bucket, fine disambiguation**: the key is intentionally loose (type+location only). Including title or price in the key would cause the same property with a slightly different title or price drift to miss. The DCS does the fine-grained work.

## Consequences

- Migration 0001 initially used a finer match_key (including title+price_bucket). Migration 0002 dropped the unique constraint and recomputed all keys with the coarse formula after testing showed cross-source duplicates weren't merging.
- The DCS is computed per candidate; with ~10 candidates per bucket this is negligible.
- `match_explanation` JSONB on `raw_listings` stores the DCS factors and classification ("Confirmed Match", "Probable Match", "New Property") for UI explainability.