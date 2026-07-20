from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from seymour_pool_engine.services.block_service import (
    get_block,
    get_blocks,
    get_block_statistics,
    synchronize_blocks,
)

router = APIRouter(prefix="/blocks", tags=["blocks"])


class BlockObservation(BaseModel):
    provider_block_key: str = Field(alias="providerBlockKey")
    pool_id: str = Field(alias="poolId")
    block_height: int = Field(alias="blockHeight")
    block_hash: str | None = Field(default=None, alias="blockHash")
    status: str = "candidate"
    confirmations: int = 0
    network_difficulty: float | None = Field(default=None, alias="networkDifficulty")
    reward: float | None = None
    miner: str | None = None
    worker: str = ""
    share_id: UUID | None = Field(default=None, alias="shareId")
    found_at: datetime = Field(alias="foundAt")
    confirmed_at: datetime | None = Field(default=None, alias="confirmedAt")
    orphaned_at: datetime | None = Field(default=None, alias="orphanedAt")
    last_checked_at: datetime | None = Field(default=None, alias="lastCheckedAt")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class BlockSyncRequest(BaseModel):
    provider: str = "miningcore"
    blocks: list[BlockObservation]


@router.get("")
def blocks(
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
    status: Annotated[str | None, Query()] = None,
    since: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query()] = 100,
) -> dict:
    try:
        return get_blocks(pool_id=pool_id, status=status, since=since, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Block inventory query failed") from exc


@router.get("/statistics")
def block_statistics(
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
) -> dict:
    try:
        return get_block_statistics(pool_id=pool_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Block statistics query failed") from exc


@router.get("/{block_id}")
def block(block_id: UUID) -> dict:
    try:
        result = get_block(block_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Block query failed") from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Block not found")
    return result


@router.post("/sync")
def sync_blocks(request: BlockSyncRequest) -> dict:
    try:
        return synchronize_blocks(
            provider_name=request.provider,
            observations=[item.model_dump() for item in request.blocks],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Block synchronization failed") from exc
