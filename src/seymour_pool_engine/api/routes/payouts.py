from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from seymour_pool_engine.services.payout_service import PayoutService

router = APIRouter(tags=["payouts"])


class PayoutItemRequest(BaseModel):
    worker_id: UUID | None = Field(default=None, alias="workerId")
    miner: str
    worker: str = ""
    destination_address: str = Field(alias="destinationAddress")
    amount: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class PayoutBatchRequest(BaseModel):
    batch_key: str = Field(alias="batchKey")
    pool_id: str = Field(alias="poolId")
    coin: str
    network: str
    source_wallet_id: UUID = Field(alias="sourceWalletId")
    minimum_payout: str = Field(default="0", alias="minimumPayout")
    requested_by: str = Field(default="api", alias="requestedBy")
    items: list[PayoutItemRequest]
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class ActorRequest(BaseModel):
    actor: str = "api"


class CompletionRequest(ActorRequest):
    transaction_id: str = Field(alias="transactionId")
    model_config = {"populate_by_name": True}


class FailureRequest(ActorRequest):
    failure_reason: str = Field(alias="failureReason")
    model_config = {"populate_by_name": True}


@router.get("/payouts/eligible")
def eligible_payouts(pool_id: str, minimum_payout: str = "0") -> list[dict[str, Any]]:
    try:
        return PayoutService().eligible(pool_id=pool_id, minimum_payout=minimum_payout)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/payouts/batches", status_code=201)
def create_payout_batch(request: PayoutBatchRequest) -> dict[str, Any]:
    try:
        values = request.model_dump()
        values["items"] = [item.model_dump() for item in request.items]
        return PayoutService().create(**values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/payouts/batches")
def list_payout_batches(
    pool_id: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    return PayoutService().list(pool_id=pool_id, limit=limit)


@router.get("/payouts/batches/{payout_batch_id}")
def get_payout_batch(payout_batch_id: UUID) -> dict[str, Any]:
    try:
        return PayoutService().get(payout_batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/payouts/batches/{payout_batch_id}/approve")
def approve_payout_batch(
    payout_batch_id: UUID, request: ActorRequest
) -> dict[str, Any]:
    return _transition(PayoutService().approve, payout_batch_id, actor=request.actor)


@router.post("/payouts/batches/{payout_batch_id}/start")
def start_payout_batch(payout_batch_id: UUID, request: ActorRequest) -> dict[str, Any]:
    return _transition(PayoutService().start, payout_batch_id, actor=request.actor)


@router.post("/payouts/batches/{payout_batch_id}/complete")
def complete_payout_batch(
    payout_batch_id: UUID, request: CompletionRequest
) -> dict[str, Any]:
    return _transition(
        PayoutService().complete, payout_batch_id,
        actor=request.actor, transaction_id=request.transaction_id,
    )


@router.post("/payouts/batches/{payout_batch_id}/fail")
def fail_payout_batch(payout_batch_id: UUID, request: FailureRequest) -> dict[str, Any]:
    return _transition(
        PayoutService().fail, payout_batch_id,
        actor=request.actor, failure_reason=request.failure_reason,
    )


@router.post("/payouts/batches/{payout_batch_id}/cancel")
def cancel_payout_batch(payout_batch_id: UUID, request: ActorRequest) -> dict[str, Any]:
    return _transition(PayoutService().cancel, payout_batch_id, actor=request.actor)


@router.get("/payouts/batches/{payout_batch_id}/events")
def payout_events(payout_batch_id: UUID) -> list[dict[str, Any]]:
    return PayoutService().events(payout_batch_id)


def _transition(call: Any, payout_batch_id: UUID, **values: Any) -> dict[str, Any]:
    try:
        return call(payout_batch_id=payout_batch_id, **values)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
