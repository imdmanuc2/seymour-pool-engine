from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from seymour_pool_engine.services.coinbase_maturity_service import (
    CoinbaseMaturityService,
)

router = APIRouter(tags=["coinbase-maturity"])


class MaturityPolicyRequest(BaseModel):
    required_confirmations: int = Field(alias="requiredConfirmations")
    enabled: bool = True
    actor: str = "api"
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class MaturityObservationRequest(BaseModel):
    block_id: UUID = Field(alias="blockId")
    pool_id: str = Field(alias="poolId")
    coin: str
    network: str
    block_height: int = Field(alias="blockHeight")
    block_hash: str | None = Field(default=None, alias="blockHash")
    confirmations: int = 0
    observed_tip_height: int | None = Field(default=None, alias="observedTipHeight")
    orphaned: bool = False
    actor: str = "api"
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


@router.get("/coinbase-maturity/policies")
def list_maturity_policies() -> list[dict[str, Any]]:
    return CoinbaseMaturityService().policies()


@router.put("/coinbase-maturity/policies/{coin}/{network}")
def set_maturity_policy(
    coin: str, network: str, request: MaturityPolicyRequest
) -> dict[str, Any]:
    try:
        return CoinbaseMaturityService().set_policy(
            coin=coin, network=network, **request.model_dump()
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/coinbase-maturity/observations")
def observe_coinbase_maturity(
    request: MaturityObservationRequest,
) -> dict[str, Any]:
    try:
        return CoinbaseMaturityService().observe(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/coinbase-maturity/records")
def list_maturity_records(
    pool_id: str | None = None, status: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    try:
        return CoinbaseMaturityService().records(
            pool_id=pool_id, status=status, limit=limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/coinbase-maturity/summary")
def maturity_summary(pool_id: str | None = None) -> dict[str, Any]:
    return CoinbaseMaturityService().summary(pool_id=pool_id)
