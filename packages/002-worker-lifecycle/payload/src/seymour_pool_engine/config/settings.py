from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="SEYMOUR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    product_name: str = "Seymour Pool Engine"
    version: str = "0.1.0"
    api_version: str = "v1"
    environment: str = "development"

    bind_host: str = "127.0.0.1"
    bind_port: int = 8561
    log_level: str = "info"

    display_name: str = "Seymour Pool"
    instance_id: str | None = None
    identity_file: Path = Path("/var/lib/seymour-pool-engine/installation-id")

    engine_database_url: str = Field(
        default="postgresql://seymour_engine:CHANGE_ME@127.0.0.1:5432/seymour_pool_engine"
    )
    miningcore_database_url: str | None = None
    miningcore_api_url: str = "http://127.0.0.1:4000"
    worker_active_window_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
