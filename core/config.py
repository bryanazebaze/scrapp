"""Application configuration loaded from environment / .env file.

Centralizes every previously-hardcoded value: the database URL (was in
core/database.py), the API host/port, the scraper delay range, the proxy,
CORS origins, log level, and Notch Pay keys.

Import `settings` from this module instead of reading os.environ directly.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Database ---
    database_url: str = "postgresql://immo_user:1234@localhost/immo_db"

    # --- API server ---
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "*"

    # --- Scrapers ---
    scraper_delay_min: float = 2.0
    scraper_delay_max: float = 5.0
    http_proxy: str | None = None
    https_proxy: str | None = None

    # --- AI / Qwen ---
    qwen_api_key: str = "sk-ws-H.XILXMY.FtqY.MEUCIQCCuhPdAc1bJ6BouavWhfsLvzEqsV9jFJw17-U4GYmx9gIgeeww0tTMv_ddd1Qryo85yOIGAI7f2HQM9qhjkVDjWAI"
    qwen_model: str = "qwen3.6-flash"
    qwen_base_url: str = "https://ws-711m66u5kgmuf9cg.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"

    # --- Logging ---
    log_level: str = "INFO"

    # --- Nextpay / Notch Pay ---
    notchpay_public_key: Optional[str] = None
    notchpay_private_key: Optional[str] = None
    notchpay_hash_key: Optional[str] = None

    # --- Auth (JWT for end-users and admins) ---
    # HS256 signing secret for issued JWTs. Override via .env in production.
    jwt_secret: str = "centralimmo-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours
    # Default password for the two seeded admin accounts (changed on first login
    # in a real deployment). Override via .env.
    admin_seed_password: str = "Test123*#"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def scraper_delay_range(self) -> tuple[float, float]:
        lo, hi = self.scraper_delay_min, self.scraper_delay_max
        return (min(lo, hi), max(lo, hi))

    @property
    def notchpay_keys_loaded(self) -> bool:
        """True if the public key is available (minimum required to call Notch Pay)."""
        return bool(self.notchpay_public_key)

    def load_notchpay_keys_from_file(self) -> None:
        """Read Notch Pay keys from ``Payment/.key`` if env vars aren't set.

        The file format is a label line (e.g. ``Public:`` or ``private :``)
        followed by one or more blank lines and then the key value on its
        own line.  We parse by tracking the most-recent label and assigning
        the next non-empty, non-label line as its value.

        Missing file is a warning, not a crash — payment endpoints will
        return 503 when ``notchpay_keys_loaded`` is False.
        """
        if self.notchpay_keys_loaded:
            return  # already set via env vars

        key_file = PROJECT_ROOT / "Payment" / ".key"
        if not key_file.exists():
            logger.warning("Notch Pay key file not found at %s", key_file)
            return

        try:
            current_label: str | None = None
            for line in key_file.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                lower = stripped.lower()

                # Detect label lines
                if lower.startswith("public"):
                    current_label = "public"
                    continue
                elif lower.startswith("private"):
                    current_label = "private"
                    continue
                elif lower.startswith("hash"):
                    current_label = "hash"
                    continue

                # Non-empty line after a label = the key value
                if stripped and current_label is not None:
                    if current_label == "public" and not self.notchpay_public_key:
                        self.notchpay_public_key = stripped
                    elif current_label == "private" and not self.notchpay_private_key:
                        self.notchpay_private_key = stripped
                    elif current_label == "hash" and not self.notchpay_hash_key:
                        self.notchpay_hash_key = stripped
                    current_label = None
        except Exception as exc:
            logger.warning("Error reading Notch Pay key file: %s", exc)


settings = Settings()
settings.load_notchpay_keys_from_file()