from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from seymour_pool_engine.services.wallet_service import WalletService

router = APIRouter(tags=["wallets"])


class WalletCreateRequest(BaseModel):
    wallet_key: str = Field(alias="walletKey")
    pool_id: str | None = Field(default=None, alias="poolId")
    coin: str
    network: str
    purpose: str
    address: str
    status: str = "active"
    descriptor_reference: str | None = Field(default=None, alias="descriptorReference")
    secret_reference: str | None = Field(default=None, alias="secretReference")
    created_by: str = Field(default="api", alias="createdBy")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class ActorRequest(BaseModel):
    actor: str = "api"


class WorkerPayoutRequest(BaseModel):
    network: str
    address: str
    changed_by: str = Field(default="api", alias="changedBy")
    model_config = {"populate_by_name": True}


@router.get("/wallets")
def list_wallets(
    coin: str | None = None,
    purpose: str | None = None,
) -> list[dict[str, Any]]:
    return WalletService().list(coin=coin, purpose=purpose)


@router.post("/wallets", status_code=201)
def create_wallet(request: WalletCreateRequest) -> dict[str, Any]:
    try:
        return WalletService().create(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Wallet creation failed") from exc


@router.get("/wallets/{wallet_id}")
def get_wallet(wallet_id: UUID) -> dict[str, Any]:
    try:
        return WalletService().get(wallet_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/wallets/{wallet_id}/validate")
def validate_wallet(wallet_id: UUID, request: ActorRequest) -> dict[str, Any]:
    try:
        return WalletService().validate(wallet_id=wallet_id, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/wallets/{wallet_id}/{status}")
def change_wallet_status(wallet_id: UUID, status: str, request: ActorRequest) -> dict[str, Any]:
    try:
        return WalletService().change_status(
            wallet_id=wallet_id, status=status, actor=request.actor
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/wallets/{wallet_id}/events")
def wallet_events(wallet_id: UUID) -> list[dict[str, Any]]:
    return WalletService().events(wallet_id)


@router.get("/workers/{worker_id}/payout-addresses")
def worker_payout_addresses(worker_id: UUID) -> list[dict[str, Any]]:
    return WalletService().worker_payouts(worker_id)


@router.put("/workers/{worker_id}/payout-addresses/{coin}")
def set_worker_payout_address(
    worker_id: UUID,
    coin: str,
    request: WorkerPayoutRequest,
) -> dict[str, Any]:
    try:
        return WalletService().set_worker_payout(
            worker_id=worker_id,
            coin=coin,
            network=request.network,
            address=request.address,
            changed_by=request.changed_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
