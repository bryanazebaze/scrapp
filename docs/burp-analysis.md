# Burp Suite Analysis — Findings & Applied Changes

## Sources analyzed

- `Burp/Mapoile-Arch.txt` — Mapiole site architecture (PHP 8.0.30, Bootstrap 5, server-rendered HTML)
- `Burp/Kassastay.txt` — Kasastay (3-line summary, Next.js)

## Mapiole findings

### Site architecture
- **Stack**: PHP 8.0.30, Bootstrap 5, server-rendered HTML (no SPA framework)
- **Cookies**: `hcdn` + `PHPSESSID` — session reuse handles this; no CSRF/Auth on read endpoints
- **No public REST API**: the site is entirely server-rendered HTML

### Hidden AJAX endpoints (insufficient for scraping)
| Endpoint | Returns | Verdict |
|----------|---------|---------|
| `search_home.inc.php` | `{id, title, country, type}` | Insufficient — no price, no images, no details |
| `searchfilter.inc.php` | Counts only | Useless for listing extraction |
| `searchsuggestions.inc.php` | Location name suggestions | Could help location autocomplete, not needed for scraping |

**Conclusion**: Keep HTML scraping. The AJAX endpoints return too little data to replace it.

### Applied changes (from Burp findings)

1. **Pagination**: Mapiole uses `?page=N` (7 pages documented in Burp). The old scraper hard-capped to 5 listings with no pagination. The refactored `MapioleAdapter.fetch_listings()` iterates `?page=1..N`.

2. **Missing field extraction** (Burp documents these selectors, old scraper missed them):
   - **Rooms/baths/area**: `span.prop-card__meta-item strong` on listing cards, `div.ab-keyfact` on detail pages
   - **GPS coordinates**: `lat`/`lng` in Leaflet `<script>` block on detail pages
   - **Amenities**: `div.ab-amenity` containers on detail pages
   - **Property ID**: `input[name="product_id"]` hidden field

   The refactored `MapioleAdapter.fetch_details()` extracts all of these.

### Noted but not scraping-relevant
- PayPal client-id found inlined in Mapoile detail page (noted, not relevant to scraping)
- Exchange rate API key inlined (noted, not relevant)

## Kasastay findings

### Site architecture
- **Stack**: Next.js (React SSR)
- **Image URLs**: proxied via `/_next/image?url=...` — already decoded in `kasastay.py:79-82` (kept, moved to `scrapers/utils.py` as `decode_next_image_url()`)

### Likely JSON routes (unverified)
Next.js apps typically expose `_next/data/{buildId}/{page}.json` routes. The refactored `KasastayAdapter`:
1. Extracts `buildId` from the `__NEXT_DATA__` script tag (`_discover_build_id()`)
2. Probes `_next/data/{buildId}/{page}.json` (`_try_next_data()`)
3. Falls back to HTML scraping if the JSON route is unavailable

### Action item: capture Kasastay traffic
`Burp/Kassastay.txt` is only 3 lines — insufficient for a thorough analysis. **A Burp capture of Kasastay browsing is flagged as a follow-up task** to verify the `_next/data` routes and document any anti-bot measures.

## General findings

- **No GraphQL anywhere** in either site
- **No `.har` or `.http` files** found in the repository
- **No API rate-limiting headers** observed on either site (but jittered delays + browser headers are still good practice)

## Anti-bot hardening applied

Both adapters now use `BaseFetchMixin` (`scrapers/http_mixin.py`):
- Rotating User-Agent pool (5 current Chrome/Firefox UAs)
- `Accept`, `Accept-Language: fr-FR`, `Sec-Fetch-*` headers
- Jittered delays: `uniform(2.0, 5.0)`s between requests (was fixed 1s)
- `requests.Session` reuse (cookies persisted, hcdn/PHPSESSID handled)
- `urllib3.util.Retry(total=3, backoff_factor=2, status_forcelist=[429,500,502,503,504])`
- `robots.txt` checked via `urllib.robotparser.RobotFileParser` before each request
- Optional proxy via `HTTP_PROXY`/`HTTPS_PROXY` env vars