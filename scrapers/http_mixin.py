"""BaseFetchMixin — shared HTTP layer with anti-bot hardening.

Applied by EVERY adapter (dedicated + universal). Centralizes what the old
scrapers did inconsistently or not at all:

- browser-like headers (the old HTML fetches at mapiole.py:89 / kasastay.py:104
  sent the default `python-requests` User-Agent — a red flag for bot detection)
- jittered delays between requests (replaces the fixed `time.sleep(1)` at
  mapiole.py:159 / kasastay.py:183)
- one `requests.Session` per adapter with persisted cookies (so hcdn /
  PHPSESSID sessions on Mapiole stay warm)
- retries with exponential backoff on 429/5xx
- optional outbound proxy via env or per-source crawl_config
- robots.txt respect (fetched once, checked before every request)
- 15s timeouts

Usage: `class MapioleAdapter(SourceAdapter, BaseFetchMixin): ...` and call
`self.fetch(url)` / `self.session` instead of `requests.get(...)`.
"""
from __future__ import annotations

import random
import time
import urllib.robotparser
from urllib.parse import urlparse, urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import settings


# A small pool of current, plausible browser User-Agents. One is picked per
# adapter instance and reused for its lifetime (rotating per-request looks
# more bot-like, not less).
USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
]

_BOT_BLOCK_PRICE_PATHS = False  # robots policy is per-instance, see below


class BaseFetchMixin:
    """Mixin providing hardened HTTP fetching for source adapters."""

    # Subclasses may override.
    request_timeout: int = 15
    max_retries: int = 3

    def init_fetch(self, base_url: str | None = None, crawl_config: dict | None = None) -> None:
        """Call from the adapter __init__ to build the session and load
        robots.txt. `crawl_config` is the per-source config from the sources
        table (may override delays / proxy / headers)."""
        self._base_url = base_url or getattr(self, "base_url", "")
        self._crawl_config = crawl_config or {}
        self._user_agent = random.choice(USER_AGENT_POOL)
        self.session = requests.Session()
        self.session.headers.update(self._default_headers())
        retry = Retry(
            total=self.max_retries,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        proxies = self._resolve_proxies()
        if proxies:
            self.session.proxies.update(proxies)

        self._robots = self._load_robots()

    # ----- headers -----
    def _default_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self._user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "application/json;q=0.8,*/*;q=0.7",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": self._base_url or "",
        }

    # ----- proxies -----
    def _resolve_proxies(self) -> dict[str, str]:
        cfg_proxy = self._crawl_config.get("proxy_url")
        if cfg_proxy:
            return {"http": cfg_proxy, "https": cfg_proxy}
        proxies: dict[str, str] = {}
        if settings.http_proxy:
            proxies["http"] = settings.http_proxy
        if settings.https_proxy:
            proxies["https"] = settings.https_proxy
        return proxies

    # ----- robots.txt -----
    def _load_robots(self) -> urllib.robotparser.RobotFileParser | None:
        if not self._base_url:
            return None
        rp = urllib.robotparser.RobotFileParser()
        robots_url = urljoin(self._base_url, "/robots.txt")
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception:
            # If robots.txt is unreachable, allow but be conservative.
            return None
        return rp

    def _robots_allows(self, url: str) -> bool:
        if self._robots is None:
            return True
        try:
            return self._robots.can_fetch(self._user_agent, url)
        except Exception:
            return True

    # ----- delays -----
    def _polite_sleep(self) -> None:
        lo, hi = settings.scraper_delay_range
        cfg = self._crawl_config.get("delay_range")
        if isinstance(cfg, (list, tuple)) and len(cfg) == 2:
            lo, hi = float(cfg[0]), float(cfg[1])
        time.sleep(random.uniform(lo, hi))

    # ----- the fetch primitive -----
    def fetch(self, url: str, *, referer: str | None = None,
              timeout: int | None = None) -> requests.Response | None:
        """GET `url` with browser headers, robots check, polite delay, retries.

        Returns the Response or None on failure. Honors robots.txt: if the
        path is disallowed, returns None and logs a warning instead of
        fetching."""
        if not self._robots_allows(url):
            print(f"[fetch] robots.txt disallows {url} — skipping")
            return None
        self._polite_sleep()
        headers = {}
        if referer:
            headers["Referer"] = referer
            headers["Sec-Fetch-Site"] = "same-origin"
        try:
            resp = self.session.get(url, headers=headers,
                                     timeout=timeout or self.request_timeout)
            if resp.status_code >= 400:
                print(f"[fetch] {url} -> HTTP {resp.status_code}")
            return resp
        except requests.RequestException as e:
            print(f"[fetch] error on {url}: {e}")
            return None

    def fetch_text(self, url: str, *, referer: str | None = None) -> str | None:
        """Convenience: GET and return response.text (decoded), or None."""
        resp = self.fetch(url, referer=referer)
        if resp is None or resp.status_code >= 400:
            return None
        return resp.text

    def head_ok(self, url: str) -> bool:
        """Lightweight check that a URL is reachable (used by the universal
        scraper to verify image URLs)."""
        try:
            r = self.session.head(url, timeout=10, allow_redirects=True)
            return r.status_code < 400
        except requests.RequestException:
            return False