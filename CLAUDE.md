# CLAUDE.md — Project Conventions for CentralImmo

## Project overview

CentralImmo is a real-estate aggregation and market-intelligence platform for Cameroon. Backend: FastAPI + SQLAlchemy + PostgreSQL. Frontend: Flutter (Riverpod + go_router + Dio). Scrapers: Python (requests + BeautifulSoup).

## Repository layout

```
scrapp/
├── core/           — backend logic (models, ingest, matcher, analytics, scoring, scheduler, config)
├── scrapers/       — source adapters (Mapiole, Kasastay, Universal, BaseFetchMixin, extractors, confidence)
├── api/            — FastAPI routers (annonces, search, neighborhoods, admin, health)
├── alembic/        — database migrations
├── docs/           — architecture docs + ADRs + Burp analysis + API reference
├── immo_app/       — Flutter app (lib/theme, lib/models, lib/services, lib/providers, lib/screens)
├── main.py         — scraper orchestrator (CLI: crawl, crawl --source, crawl --max-pages)
├── main_api.py     — FastAPI app (routers + CORS + scheduler startup)
├── cli.py          — manual triggers (crawl, refresh, analytics, jobs, universal)
└── requirements.txt
```

## Key conventions

### Data model (never violate)
- `raw_listings` is **immutable** — never UPDATE after insert. Re-crawls become `listing_history` events.
- `listing_history` is **append-only** — never UPDATE or DELETE. Price/availability changes are new rows.
- `canonical_properties.match_key` is **coarse** (type+city+neighborhood) and **NOT unique** — multiple properties share a key; the DCS disambiguates.
- `raw_listings.images_raw` stores **original URLs** (canonical record); `image_cache` is a cache.
- `raw_listings.location_raw` preserves the verbatim string; `canonical_properties.location_id` is the resolved pointer.

### Scraper framework
- All adapters implement `SourceAdapter` (ABC in `scrapers/base.py`): `fetch_listings()`, `fetch_details()`, `normalize_data()`, `validate_data()`.
- All adapters use `BaseFetchMixin` (`scrapers/http_mixin.py`) for anti-bot: browser headers, jittered delays, session reuse, retries, robots.txt.
- Dedicated adapters (Mapiole, Kasastay) auto-promote all listings. Universal adapter gates on confidence (≥0.75 auto, 0.40-0.74 pending, <0.40 rejected).
- `RawListingDraft` (dataclass in `scrapers/drafts.py`) is the canonical intermediate between scrapers and ingest.

### Ingest pipeline (`core/ingest.py`)
- Idempotent on `url_hash = sha256(url_source)`. Re-crawls compare to latest `listing_history` event; append only on diff.
- Pending listings do NOT create canonical properties (prevents orphan canonicals).
- `promote_raw_listing()` handles admin review: approve creates/links canonical + backdates `first_seen` to `crawled_at`.

### Analytics (`core/analytics.py` + `core/scoring.py`)
- Scores are 0-10, computed from platform data only (no external demographics).
- `recompute_all(db)` writes to `neighborhood_analytics` cache table. Run weekly via scheduler.
- Score functions: `premium_score` (ratio vs city median), `demand_score` (inverse days-on-market), `growth_score` (90-day trend), `activity_score` (listings/week), `luxury_score` (blend).

### API
- Routers in `api/` package, mounted by `main_api.py`.
- Server-side filtering — never filter client-side in Flutter.
- Natural-language search parses the query string server-side (`api/search.py`).
- CORS configured via `settings.cors_origins` (from `.env`).
- Scheduler starts on FastAPI startup (`lifespan` context).

### Flutter
- State: Riverpod providers in `lib/providers/providers.dart`.
- Routing: go_router in `lib/router/app_router.dart`.
- API: Dio-based `ApiClient` in `lib/services/api_client.dart`.
- Config: `lib/config.dart` reads `API_BASE_URL` via `--dart-define`.
- Theme: single source in `lib/theme/app_theme.dart`. Orange `0xFFE94E1B` primary, white-first.
- No `setState` in screens — use Riverpod providers.
- No hardcoded URLs — use `AppConfig.apiBaseUrl`.
- No `Navigator.push` — use `context.go('/path')`.

## Common commands

```bash
# Backend
cd scrapp
alembic upgrade head           # run migrations
python cli.py crawl             # crawl all active sources
python cli.py crawl --source mapiole --max-pages 3
python cli.py analytics         # recompute neighborhood scores
python cli.py jobs              # list scheduled jobs
python cli.py universal --url https://example.com  # crawl a new site
uvicorn main_api:app --reload   # start API server

# Flutter
cd immo_app
flutter pub get
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
flutter analyze
flutter build web --dart-define=API_BASE_URL=http://127.0.0.1:8000

# Database
PGPASSWORD=1234 psql -h localhost -U immo_user -d immo_db
```

## Testing notes

- No automated test suite yet. Verification is manual: run crawls, check API endpoints with curl, run analytics recompute, launch Flutter app.
- The DB is seeded with 2 sources (mapiole, kasastay) by the Alembic migration.
- Test data can be seeded manually (see the verification steps in the plan).

## What NOT to do

- Do NOT overwrite `raw_listings` rows — they are immutable.
- Do NOT add a unique constraint on `canonical_properties.match_key` — it's intentionally non-unique.
- Do NOT use `setState` in Flutter screens — use Riverpod providers.
- Do NOT hardcode API URLs in Flutter screens — use `AppConfig.apiBaseUrl`.
- Do NOT filter listings client-side — use server-side query parameters.
- Do NOT skip `robots.txt` checks in scrapers — `BaseFetchMixin` handles this.