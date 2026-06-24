# CentralImmo — Architecture

## Overview

CentralImmo is a real-estate aggregation and market-intelligence platform for Cameroon. It crawls multiple property-listing websites (Mapiole, Kasastay, and arbitrary sites via the universal fallback scraper), deduplicates them into canonical properties, tracks price/availability history, computes neighborhood market scores, and serves a Flutter frontend.

```
                    ┌─────────────────────────────────────────┐
                    │            Scheduler (APScheduler)       │
                    │  daily crawl · 6h refresh · weekly analytics│
                    └───────────────┬─────────────────────────┘
                                    │
   ┌────────────┐    ┌──────────────▼──────────────┐    ┌────────────┐
   │ Mapiole    │    │     SourceAdapter layer     │    │ Universal  │
   │ Adapter    │    │  (common interface)         │    │ Fallback   │
   │ (dedicated)│    │  BaseFetchMixin (anti-bot)  │    │ Adapter    │
   └────────────┘    └──────────────┬──────────────┘    └────────────┘
                                    │ List[RawListingDraft]
                    ┌───────────────▼───────────────┐
                    │   Ingest pipeline             │
                    │  ingest() → raw_listings →     │
                    │  match_key resolve → canonical│
                    │  → listing_history (append)    │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  Analytics services           │
                    │  City + Neighborhood scoring  │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  FastAPI (env-configured)     │
                    │  /annonces /neighborhoods     │
                    │  /search /review /admin       │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  Flutter (Riverpod, go_router,│
                    │  Dio, maps, charts)           │
                    └───────────────────────────────┘
```

## Data Model (5 core + 3 operational tables)

### Core tables

| Table | Purpose | Key constraint |
|-------|---------|----------------|
| `sources` | Website metadata (one row per scraped site) | `slug` unique |
| `raw_listings` | Immutable original scraped data | `url_hash` unique (idempotent inserts) |
| `canonical_properties` | A real-world property (many raw listings → one canonical) | `match_key` indexed (coarse bucket) |
| `listing_history` | Append-only event log (price/availability changes) | Never updated, only appended |
| `locations` | Normalized city/neighborhood reference | `UNIQUE(city, COALESCE(neighborhood,''))` |

### Operational tables

| Table | Purpose |
|-------|---------|
| `image_cache` | Optional downloaded-image cache (original URLs live in `raw_listings.images_raw`) |
| `scheduler_jobs` | State of scheduled jobs (crawl/refresh/analytics) |
| `neighborhood_analytics` | Cached city/neighborhood scores (recomputed weekly) |

### Data flow

1. **Scraper** produces `RawListingDraft` objects (dataclass: title, price, images, etc. + confidence score).
2. **Ingest pipeline** (`core/ingest.py`):
   - Computes `url_hash = sha256(url_source)`. If a `raw_listing` with that hash exists, it's a re-crawl — compare to latest `listing_history` event, append a change event only if price/availability moved.
   - New URL: resolve `location_id`, compute `match_key`, query `canonical_properties` by match_key, run composite DCS to confirm/link or create new canonical.
   - Append `first_seen` history event.
3. **Matcher** (`core/matcher.py`): `match_key` (type+city+neighborhood) for O(1) candidate retrieval, then rapidfuzz title similarity + composite DCS for disambiguation.
4. **Analytics** (`core/analytics.py` + `core/scoring.py`): weekly recompute of per-neighborhood scores into `neighborhood_analytics`.
5. **API** serves listings, search, neighborhood intelligence, admin review.
6. **Scheduler** runs daily crawls, 6h refreshes, weekly analytics recompute.

## Backend structure

```
scrapp/
├── core/
│   ├── config.py         — pydantic-settings (DATABASE_URL, CORS, delays, proxies)
│   ├── database.py       — SQLAlchemy engine + SessionLocal
│   ├── models.py         — 8 SQLAlchemy ORM models
│   ├── ingest.py         — ingest pipeline (idempotent, append-only history)
│   ├── matcher.py        — match_key + composite DCS duplicate detection
│   ├── analytics.py      — neighborhood analytics recompute
│   ├── scoring.py        — 0-10 scoring functions (premium, demand, growth, activity, luxury)
│   ├── scheduler.py      — APScheduler (daily crawl, 6h refresh, weekly analytics)
│   ├── fusion.py         — compatibility shim (legacy API)
│   ├── schemas.py        — Pydantic response models
│   └── drafts.py         — RawListingDraft dataclass
├── scrapers/
│   ├── base.py           — SourceAdapter ABC
│   ├── http_mixin.py     — BaseFetchMixin (anti-bot: headers, delays, retries, robots.txt)
│   ├── mapiole.py        — Mapiole dedicated adapter
│   ├── kasastay.py       — Kasastay dedicated adapter (+ _next/data probe)
│   ├── universal.py     — Universal fallback adapter
│   ├── extractors.py     — JSON-LD / OpenGraph / heuristic field extraction
│   ├── confidence.py     — Confidence scoring (0.40-0.75 gating)
│   ├── utils.py          — Shared helpers (price parsing, city detection, image caching)
│   └── drafts.py         — RawListingDraft dataclass
├── api/
│   ├── annonces.py       — GET /annonces (server-side filtered), /annonces/{id}, /history
│   ├── search.py         — GET /search?q= (natural-language parsing)
│   ├── neighborhoods.py  — GET /neighborhoods, /{slug}, /city/{city}, /trending/list
│   ├── admin.py          — /admin/review, /admin/sources, /admin/jobs, /admin/analytics
│   └── health.py         — GET /health
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 0001_initial_schema.py   — creates 8 tables, backfills from legacy
│       └── 0002_drop_match_key_unique.py — coarse match_key
├── main.py               — scraper orchestrator (CLI entry)
├── main_api.py           — FastAPI app (routers + CORS + scheduler startup)
├── cli.py                — manual triggers (crawl, analytics, jobs, universal)
├── requirements.txt
├── .env.example
└── alembic.ini
```

## Flutter structure

```
immo_app/lib/
├── main.dart             — ProviderScope + MaterialApp.router
├── config.dart           — API_BASE_URL (--dart-define)
├── theme/
│   ├── colors.dart       — white-first + orange 0xFFE94E1B
│   ├── typography.dart   — Display/Headline/Title/Body/Caption
│   ├── spacing.dart      — 4/8/12/16/24/32/48
│   └── app_theme.dart    — single source of truth ThemeData
├── models/
│   ├── annonce.dart      — Annonce, RawListing, ListingHistoryEvent
│   └── location.dart     — Location, NeighborhoodAnalytics
├── services/
│   └── api_client.dart   — Dio-based API client
├── providers/
│   └── providers.dart    — Riverpod providers (annonces, search, favorites, analytics)
├── router/
│   └── app_router.dart   — go_router (onboarding, home, search, property, neighborhood, favorites, map)
└── screens/
    ├── onboarding/       — 3-page carousel (shown once via SharedPreferences)
    ├── home/             — search bar, trending neighborhoods, recent listings
    ├── search/           — natural-language query + suggestions
    ├── property/         — image carousel, price history chart (fl_chart), sources, neighborhood link
    ├── neighborhood/     — price stats, 5 scores with progress bars, trend card
    ├── favorites/        — persisted via SharedPreferences
    ├── map/              — flutter_map (OSM), city-level markers
    └── widgets/
        └── annonce_card.dart — reusable listing card
```

## Configuration

Backend reads from `.env` (see `.env.example`):
- `DATABASE_URL` — PostgreSQL connection string
- `API_HOST` / `API_PORT` — FastAPI bind
- `CORS_ORIGINS` — allowed origins (comma-separated)
- `SCRAPER_DELAY_MIN` / `SCRAPER_DELAY_MAX` — jittered delay range
- `HTTP_PROXY` / `HTTPS_PROXY` — optional proxy
- `LOG_LEVEL`

Flutter:
- `API_BASE_URL` — backend URL (via `--dart-define=API_BASE_URL=http://...`)
- Android emulator: `http://10.0.2.2:8000`
- Physical device: `http://<PC-WiFi-IP>:8000`

## Getting started

```bash
# Backend
cd scrapp
cp .env.example .env  # edit credentials
pip install -r requirements.txt
alembic upgrade head   # creates tables + backfills from legacy
python cli.py crawl --source mapiole  # first crawl
python cli.py analytics  # compute neighborhood scores
uvicorn main_api:app --reload

# Flutter
cd immo_app
flutter pub get
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```