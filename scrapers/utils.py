"""Shared scraper utilities.

Removes the duplicated code between mapiole.py and kasastay.py:
- parse_prix (was duplicated at mapiole.py:58 and kasastay.py:56)
- the property-type keyword classifier (duplicated at mapiole.py:137-145
  and kasastay.py:132-140)
- the Kasastay `_next/image` URL decode (kasastay.py:79-82)
- title normalization (was in core/fusion.py:6 — relocated here since
  scrapers need it for payload building and the matcher still uses its own
  copy kept frozen for migration safety)

Images are no longer downloaded locally — the app renders original source
URLs directly via CachedNetworkImage (see ADR-005).
"""
from __future__ import annotations

import re
import unicodedata
import urllib.parse


# --------------------------------------------------------------------------- #
# Text / price
# --------------------------------------------------------------------------- #
def normalize_text(text: str | None) -> str:
    """Lowercase + strip accents + normalize dashes to spaces + collapse
    whitespace, for title comparison and slug building. Dashes and spaces are
    treated as equivalent so "Mvog-Mbi" and "Mvog Mbi" match."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    s = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = re.sub(r"[-–—]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slugify(text: str | None) -> str:
    n = normalize_text(text)
    n = re.sub(r"[^a-z0-9]+", "-", n)
    return n.strip("-")


def parse_price(price_text: str | None, currency_hint: str = "XAF",
                *, min_value: int = 0, reject_per_sqm: bool = False) -> int | None:
    """Extract an integer price from a free-form price string.

    Handles formats like "150 000 FCFA", "12.000 FCFA/mensuel", "Total:
    55.000.000 FCFA", "XAF 150000". Strips thousand separators (space, dot,
    comma) and returns the integer. Returns None if no digits found.

    Guards against absurdly large numbers (e.g. when the text node contains
    dates or timestamps alongside the price): if the extracted digits exceed
    100 billion (10^11), return None — no real-estate price in Central Africa
    exceeds that.

    Keyword args:
      min_value:      reject values below this floor (default 0 — preserves
                      existing behavior for area/room-count callers). Price
                      callers should pass min_value=1000 to reject 0 and
                      near-zero parse failures.
      reject_per_sqm: if True, return None when the text contains a per-square-
                      meter marker (/m², /m2, per sqm). Per-sqm unit prices
                      must not be stored as total prices. Price callers should
                      pass reject_per_sqm=True; area callers must NOT (area
                      values like "50 m²" legitimately contain the marker).
    """
    if not price_text:
        return None
    if reject_per_sqm and _PER_SQM_RE.search(price_text):
        return None
    # Try to find a price-like pattern first: digits with separators + currency.
    # This avoids concatenating digits from dates, timestamps, or other numbers
    # that appear in the same text node.
    # Match: optional currency prefix, then grouped digits with spaces/dots/commas
    # e.g. "45 000 000 XAF", "XAF 150000", "12.000.000 FCFA", "55.000.000"
    m = re.search(
        r"(?:XAF|FCFA|CFA)?\s*([\d][\d\s.,]{2,})\s*(?:XAF|FCFA|CFA)?",
        price_text,
    )
    if m:
        digits = re.sub(r"[^\d]", "", m.group(1))
    else:
        # Fallback: strip all non-digits (old behavior, but with a sanity cap).
        digits = re.sub(r"[^\d]", "", price_text)
    if not digits:
        return None
    try:
        val = int(digits)
    except ValueError:
        return None
    if val < min_value:
        return None
    # Sanity cap: no real-estate price in Cameroon exceeds 100 billion XAF.
    if val > 100_000_000_000:
        return None
    return val


# Per-square-meter markers that indicate a unit price, not a total. Such
# values must not be stored as price_parsed (they would inflate land/commercial
# listings by the area factor).
_PER_SQM_RE = re.compile(r"/\s*m[²2]\b|per\s*(?:sqm|square\s*m)", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Property-type classification
# --------------------------------------------------------------------------- #
_TYPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Appartement", ["appartement", "apartment", "studio", "flat"]),
    ("Maison", ["maison", "villa", "house", "duplex", "bungalow"]),
    ("Terrain", ["terrain", "land", "plot", "lot"]),
    ("Bureau", ["bureau", "office", "commercial", "shop", "magasin"]),
    ("Chambre", ["chambre", "room", "single room"]),
]


def classify_property_type(text: str | None, fallback: str = "Autre") -> str:
    """Infer a property type from title/url/description text.

    Order matters: checked in declaration order so 'studio' maps to
    Appartement before the generic Maison branch. Returns `fallback` if no
    keyword matches.
    """
    if not text:
        return fallback
    low = text.lower()
    for label, keywords in _TYPE_KEYWORDS:
        if any(kw in low for kw in keywords):
            return label
    return fallback


# --------------------------------------------------------------------------- #
# Image handling
# --------------------------------------------------------------------------- #
def decode_next_image_url(src: str, base_url: str) -> str | None:
    """Kasastay (Next.js) hides the real image URL behind a
    `/_next/image?url=<encoded>&w=...&q=...` proxy. Recover the real URL."""
    if "_next/image" in src and "url=" in src:
        try:
            encoded = src.split("url=")[1].split("&")[0]
            return urllib.parse.unquote(encoded)
        except Exception:
            return None
    if src.startswith("http"):
        return src
    if src.startswith("/"):
        return base_url.rstrip("/") + src
    return None


def looks_like_logo(src: str) -> bool:
    low = src.lower()
    return any(tok in low for tok in ("logo", "icon", "avatar", "favicon", "sprite"))


# Tracking / analytics pixels that sneak into <img> tags and must NOT be
# treated as property images.
_TRACKING_HOSTS = (
    "facebook.com/tr", "facebook.net", "googletagmanager.com",
    "google-analytics.com", "doubleclick.net", "hotjar.com", "clarity.ms",
    "pixel", "analytics", "scorecardresearch", "quantserve.com",
)


def looks_like_tracking(src: str) -> bool:
    low = src.lower()
    return any(tok in low for tok in _TRACKING_HOSTS)


def is_real_image(src: str) -> bool:
    """True if src is a plausible property image (not a logo/tracking pixel)."""
    if not src:
        return False
    return not (looks_like_logo(src) or looks_like_tracking(src))


# --------------------------------------------------------------------------- #
# Cameroon location dictionary
# --------------------------------------------------------------------------- #
CAMEROON_CITIES = [
    "Douala", "Yaoundé", "Bafoussam", "Garoua", "Maroua", "Bamenda",
    "Ngaoundéré", "Bertoua", "Ebolowa", "Kribi", "Limbe", "Buea",
    "Nkongsamba", "Nkongssamba", "Edéa", "Kumba",
    "Mbalmayo", "Okola", "Dschang", "Fontong", "Tiko", "Mutengene",
]

# Neighborhood database: (display_name, city, lat, lng).
# Coordinates are approximate centroids — good enough for analytics grouping
# and map display; they are NOT survey-grade. When a new neighborhood is
# discovered, add it here so resolve_location can assign a city + coords.
_NEIGHBORHOODS: list[tuple[str, str, float, float]] = [
    # Douala (~4.05N, 9.70E)
    ("Akwa", "Douala", 4.0597, 9.7036),
    ("Bonanjo", "Douala", 4.0463, 9.6981),
    ("Bonapriso", "Douala", 4.0389, 9.7047),
    ("Bonamoussadi", "Douala", 4.0500, 9.7333),
    ("Deido", "Douala", 4.0653, 9.7131),
    ("Kotto", "Douala", 4.0431, 9.7189),
    ("Makepe", "Douala", 4.0500, 9.7500),
    ("Logbessou", "Douala", 4.0833, 9.7000),
    ("Nkoulouloun", "Douala", 4.0667, 9.7167),
    ("Bonabéri", "Douala", 4.0750, 9.6833),
    ("New Bell", "Douala", 4.0333, 9.7167),
    ("Bali", "Douala", 4.0583, 9.6917),
    ("Mboppi", "Douala", 4.0417, 9.7083),
    ("Bassa", "Douala", 4.0500, 9.7000),
    ("Nylon", "Douala", 4.0333, 9.7333),
    ("Dakar", "Douala", 4.0333, 9.7000),
    ("Bercy", "Douala", 4.0167, 9.7333),
    ("Yassa", "Douala", 3.9833, 9.8000),
    ("Ndokoti", "Douala", 4.0333, 9.7500),
    ("Logpom", "Douala", 4.0750, 9.7167),
    ("Japoma", "Douala", 4.0167, 9.7833),
    ("Bonabéri", "Douala", 4.0750, 9.6833),
    # Yaoundé (~3.87N, 11.52E)
    ("Bastos", "Yaoundé", 3.8833, 11.5167),
    ("Mvog-Mbi", "Yaoundé", 3.8500, 11.5000),
    ("Mendong", "Yaoundé", 3.8333, 11.4833),
    ("Odza", "Yaoundé", 3.8167, 11.5333),
    ("Mfandena", "Yaoundé", 3.8833, 11.5000),
    ("Emana", "Yaoundé", 3.8667, 11.4667),
    ("Ngoa-Ekelle", "Yaoundé", 3.8633, 11.5133),
    ("Bruxelles", "Yaoundé", 3.8667, 11.5000),
    ("Madagascar", "Yaoundé", 3.8667, 11.5167),
    ("Cité Verte", "Yaoundé", 3.8667, 11.5050),
    ("Simbock", "Yaoundé", 3.8333, 11.5333),
    ("Nsam", "Yaoundé", 3.8667, 11.5167),
    ("Nkolbisson", "Yaoundé", 3.8833, 11.4500),
    ("Biyem Assi", "Yaoundé", 3.8500, 11.4833),
    ("Ngombé", "Yaoundé", 3.8500, 11.5000),
    ("Mokolo", "Yaoundé", 3.8667, 11.5000),
    ("Elig-Edzoa", "Yaoundé", 3.8667, 11.5167),
    ("Etoudi", "Yaoundé", 3.9000, 11.5167),
    ("Mvan", "Yaoundé", 3.8333, 11.5000),
    ("Mvog-Ada", "Yaoundé", 3.8500, 11.5167),
    ("Tsinga", "Yaoundé", 3.8833, 11.5167),
    ("Olembe", "Yaoundé", 3.9167, 11.5833),
    ("Ahala", "Yaoundé", 3.8500, 11.5500),
    ("Ngousso", "Yaoundé", 3.8500, 11.5167),
    ("Odja", "Yaoundé", 3.8333, 11.5167),
    ("Nkoabang", "Yaoundé", 3.8833, 11.5500),
    ("Centre", "Yaoundé", 3.8667, 11.5167),
]

CAMEROON_NEIGHBORHOODS = [n[0] for n in _NEIGHBORHOODS]

# Normalized-neighborhood -> city, for inferring a city when the raw text
# contains only a neighborhood name (no city). Keyed by normalize_text(name).
NEIGHBORHOOD_TO_CITY: dict[str, str] = {
    normalize_text(n[0]): n[1] for n in _NEIGHBORHOODS
}

# Normalized-neighborhood -> (lat, lng), for populating locations.lat/lng.
_NEIGHBORHOOD_COORDS: dict[str, tuple[float, float]] = {
    normalize_text(n[0]): (n[2], n[3]) for n in _NEIGHBORHOODS
}


def detect_city(location: str | None) -> str | None:
    if not location:
        return None
    low = normalize_text(location)
    for c in CAMEROON_CITIES:
        if normalize_text(c) in low:
            return c
    return None


def infer_city_from_neighborhood(location: str | None) -> str | None:
    """If the text contains a known neighborhood but no explicit city name,
    infer the city from the neighborhood→city mapping. Returns None if no
    known neighborhood is found."""
    if not location:
        return None
    low = normalize_text(location)
    for nb_key, city in NEIGHBORHOOD_TO_CITY.items():
        if nb_key and nb_key in low:
            return city
    return None


def neighborhood_coords(neighborhood: str | None,
                         city: str | None) -> tuple[float | None, float | None]:
    """Look up approximate (lat, lng) for a known neighborhood/city pair.
    Returns (None, None) when no coordinates are available."""
    if not neighborhood:
        return None, None
    coords = _NEIGHBORHOOD_COORDS.get(normalize_text(neighborhood))
    if coords:
        return coords
    return None, None


def detect_city_text(soup) -> str | None:
    """Scan a parsed page's short text tags for a known Cameroon city name.

    Mirrors the legacy kasastay.py:148-158 fallback: walk span/p/div tags,
    return the first short (<100 char) text containing a known city.
    """
    for tag in soup.find_all(["span", "p", "div"]):
        text = tag.get_text(strip=True)
        if not text or len(text) >= 100:
            continue
        city = detect_city(text)
        if city:
            return text
    return None


# Keywords that signal a property title fragment, not a neighborhood name.
# Used to reject heuristic neighborhood extraction from title strings.
_BAD_NEIGHBORHOOD_KEYWORDS = (
    "vente", "vendre", "louer", "location", "terrain", "appartement",
    "maison", "chambre", "studio", "bureau", "commercial", "espace",
    "salle", "magnifique", "meuble", "titre", "disponible", "cherche",
)


def detect_neighborhood(location: str | None, city: str | None) -> str | None:
    if not location:
        return None
    low = normalize_text(location)
    for nb in CAMEROON_NEIGHBORHOODS:
        if normalize_text(nb) in low:
            return nb
    # Heuristic: text before a separator that isn't the city and doesn't
    # look like a property title fragment (e.g. "Terrain à vendre" is NOT
    # a neighborhood, even if it appears before a comma).
    for sep in (",", " - ", "–", "/"):
        if sep in location:
            head = location.split(sep)[0].strip()
            if head and (not city or normalize_text(city) not in normalize_text(head)):
                low_head = normalize_text(head)
                if not any(kw in low_head for kw in _BAD_NEIGHBORHOOD_KEYWORDS):
                    return head
                break
            break
    return None


# --------------------------------------------------------------------------- #
# URL normalization (for dedup hashing)
# --------------------------------------------------------------------------- #
def normalize_url(url: str | None) -> str:
    """Normalize a URL for dedup hashing: lowercase scheme+host, strip leading
    'www.', drop trailing slash, sort query params, drop fragment. The original
    URL is still stored verbatim in raw_listings.url_source; this is only used
    to compute url_hash so the same property under slightly different URLs
    (query-param reordering, http vs https, trailing slash) collapses to one
    raw_listing row."""
    if not url:
        return ""
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    parts = urlsplit(url)
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parts.path.rstrip("/") or "/"
    if parts.query:
        qs = urlencode(sorted(parse_qsl(parts.query)))
    else:
        qs = ""
    return urlunsplit((scheme, netloc, path, qs, ""))