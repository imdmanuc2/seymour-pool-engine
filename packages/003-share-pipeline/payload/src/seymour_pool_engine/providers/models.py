from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ComponentState = Literal["online", "offline", "disabled", "degraded", "unknown"]


class ComponentCheck(BaseModel):
    component: str
    status: ComponentState
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)


class ProviderStatus(BaseModel):
    provider: str
    status: ComponentState
    observed_at: datetime = Field(alias="observedAt")
    version: str | None = None
    schema_compatible: bool = Field(alias="schemaCompatible")
    capabilities: list[str] = Field(default_factory=list)
    checks: list[ComponentCheck] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class PoolSummary(BaseModel):
    pool_id: str = Field(alias="poolId")
    connected_miners: int = Field(alias="connectedMiners")
    pool_hashrate: float = Field(alias="poolHashrate")
    shares_per_second: float = Field(alias="sharesPerSecond")
    network_hashrate: float = Field(alias="networkHashrate")
    network_difficulty: float = Field(alias="networkDifficulty")
    block_height: int = Field(alias="blockHeight")
    connected_peers: int = Field(alias="connectedPeers")
    observed_at: datetime = Field(alias="observedAt")

    model_config = {"populate_by_name": True}


class WorkerSummary(BaseModel):
    pool_id: str = Field(alias="poolId")
    miner: str
    worker: str
    hashrate: float
    shares_per_second: float = Field(alias="sharesPerSecond")
    observed_at: datetime = Field(alias="observedAt")

    model_config = {"populate_by_name": True}


class ShareSummary(BaseModel):
    provider_share_key: str = Field(alias="providerShareKey")
    pool_id: str = Field(alias="poolId")
    miner: str
    worker: str = ""
    difficulty: float
    network_difficulty: float | None = Field(default=None, alias="networkDifficulty")
    block_height: int | None = Field(default=None, alias="blockHeight")
    ip_address: str | None = Field(default=None, alias="ipAddress")
    user_agent: str | None = Field(default=None, alias="userAgent")
    created_at: datetime = Field(alias="createdAt")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}
