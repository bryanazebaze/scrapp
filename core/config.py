"""Application configuration loaded from environment / .env file.

Centralizes every previously-hardcoded value: the database URL (was in
core/database.py), the API host/port, the scraper delay range, the proxy,
CORS origins and log level.

Import `settings` from this module instead of reading os.environ directly.
"""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


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

    # --- AI / Qwen (DashScope) ---
    dashscope_api_key: str | None = None
    qwen_model: str = "qwen-plus"
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # --- Logging ---
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def scraper_delay_range(self) -> tuple[float, float]:
        lo, hi = self.scraper_delay_min, self.scraper_delay_max
        return (min(lo, hi), max(lo, hi))


settings = Settings()