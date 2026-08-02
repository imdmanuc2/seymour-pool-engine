from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StratumSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SEYMOUR_STRATUM_", env_file=".env", extra="ignore"
    )
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = Field(default=3333, ge=0, le=65535)
    idle_timeout_seconds: float = Field(default=300.0, gt=0)
    max_connections: int = Field(default=1000, ge=1)
    max_line_bytes: int = Field(default=65536, ge=1024)
    default_difficulty: float = Field(default=1024.0, gt=0)
    extranonce2_size: int = Field(default=8, ge=2, le=16)
    processing_workers: int = Field(default=8, ge=1, le=128)
    processing_queue_limit: int = Field(default=2048, ge=16, le=100000)
    database_pool_min_size: int = Field(default=2, ge=1, le=64)
    database_pool_max_size: int = Field(default=16, ge=1, le=256)
    database_pool_timeout_seconds: float = Field(default=5.0, gt=0)


@lru_cache
def get_stratum_settings() -> StratumSettings:
    return StratumSettings()
