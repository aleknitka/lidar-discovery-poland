"""Runtime settings (env prefix LDP_)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

USER_AGENT = "lidar-discovery-poland/0.1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LDP_", env_file=".env", extra="ignore")

    data_dir: Path = Field(default=Path("data"))
    public_mode: bool = False
    seeds_dir: Path = Field(default=Path("seeds"))
    default_aoi_buffer_m: float = 1000.0
    http_timeout_s: float = 60.0
    max_fetch_area_km2: float = 6.0  # "Get data for this view": viewport area limit
    max_fetch_bytes: int = 4_000_000_000  # ... and total LAZ bytes (cached + to download)
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    watch_interval_s: int = 86400
    watch_bbox: str | None = None

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def derived_dir(self) -> Path:
        return self.data_dir / "derived"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "catalog.sqlite"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.raw_dir, self.derived_dir, self.cache_dir):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
