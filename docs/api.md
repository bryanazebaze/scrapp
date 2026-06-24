# CentralImmo API Reference

Base URL: `http://<host>:8000` (default `http://127.0.0.1:8000`)

Interactive docs: `/docs` (Swagger) or `/redoc`

## Listings

### GET /annonces
Paginated listings with server-side filtering.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | int | 0 | Pagination offset |
| limit | int | 50 | Max results (1-200) |
| property_type | string | — | e.g. "Villa", "Appartement" |
| city | string | — | e.g. "Douala" |
| neighborhood | string | — | e.g. "Bastos" |
| min_price | int | — | Minimum price in XAF |
| max_price | int | — | Maximum price in XAF |
| min_bedrooms | int | — | Minimum bedrooms |
| min_area | float | — | Minimum area in sqm |

**Response**: `List[AnnonceBreve]`
```json
{
  "id": 42, "title": "Villa moderne Bastos", "property_type": "Villa",
  "price": 95000000, "currency": "XAF", "city": "Douala",
  "neighborhood": "Bastos", "location_slug": "douala-bastos",
  "bedrooms": 4, "bathrooms": 3, "area_sqm": 220.0,
  "images": ["https://..."], "best_source": "mapiole"
}
```

### GET /annonces/{id}
Full detail including sources, price history, match explanation.

**Response**: `AnnonceDetailee` (extends `AnnonceBreve` with description, sources, price_history, match_explanation, match_confidence, created_at, last_seen_at)

### GET /annonces/{id}/history
Price/availability timeline.

**Response**: `List[ListingHistoryEvent]`
```json
{
  "id": 53, "event_type": "first_seen", "price_observed": 95000000,
  "availability": "available", "observed_at": "2026-06-20T15:41:53Z",
  "diff": null
}
```

## Search

### GET /search?q=
Natural-language search.

**Example**: `GET /search?q=3-bedroom house in Bastos under 120M`

Parses bedrooms, price range, property type, city, neighborhood from the query string and returns server-filtered results.

**Response**: `List[AnnonceBreve]`

## Neighborhoods

### GET /neighborhoods
List all locations.

| Parameter | Type | Description |
|-----------|------|-------------|
| city | string | Filter by city |

**Response**: `List[Location]`

### GET /neighborhoods/{slug}
Market intelligence for one neighborhood.

| Parameter | Type | Description |
|-----------|------|-------------|
| property_type | string | Filter analytics by property type |

**Response**: `NeighborhoodAnalytics`
```json
{
  "location_id": 17, "city": "Douala", "neighborhood": "Bastos",
  "slug": "douala-bastos", "property_type": null,
  "listing_count": 8, "average_price": 86666666, "median_price": 95000000,
  "min_price": 45000000, "max_price": 120000000, "price_per_sqm": 402272.73,
  "premium_score": 7.8, "demand_score": 7.4, "growth_score": 10.0,
  "activity_score": 0.5, "luxury_score": 5.9,
  "trend_direction": "up", "trend_pct": 37.15
}
```

### GET /neighborhoods/city/{city}
Analytics for all neighborhoods in a city.

### GET /neighborhoods/trending/list
Neighborhoods ranked by growth_score.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 10 | Max results (1-50) |

## Admin

### GET /admin/review/pending
List universal-scraper listings awaiting human review.

### POST /admin/review/{raw_listing_id}
Approve or reject a pending listing.

**Body**: `{"action": "approve"}` or `{"action": "reject"}`

**Response**:
```json
{"ok": true, "review_status": "human_approved", "canonical_property_id": 42}
```

### GET /admin/sources
List all sources.

### POST /admin/sources
Create a new source.

### POST /admin/sources/{slug}/crawl
Manually trigger a crawl for one source.

### POST /admin/sources/{slug}/toggle
Activate/deactivate a source.

### POST /admin/analytics/recompute
Manually recompute all neighborhood analytics.

### GET /admin/jobs
List scheduled job states.

## Health

### GET /health
```json
{"status": "ok", "version": "3.0.0", "database": "connected", "scheduler_running": true}
```