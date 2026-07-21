from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from seymour_pool_engine.services.multi_wallet_service import MultiWalletService

router = APIRouter(tags=["multi-wallet-operations"])


class AssignmentRequest(BaseModel):
    wallet_id: UUID = Field(alias="walletId")
    assignment_scope: str = Field(alias="assignmentScope")
    scope_key: str = Field(default="*", alias="scopeKey")
    purpose: str
    priority: int = 100
    enabled: bool = True
    created_by: str = Field(default="api", alias="createdBy")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class PolicyRequest(BaseModel):
    coin: str
    network: str
    assignment_scope: str = Field(alias="assignmentScope")
    scope_key: str = Field(default="*", alias="scopeKey")
    purpose: str
    strategy: str = "priority"
    allow_failover: bool = True
    minimum_health_status: str = "healthy"
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class ReserveRequest(BaseModel):
    minimum_balance: Decimal = Field(alias="minimumBalance")
    target_balance: Decimal | None = Field(default=None, alias="targetBalance")
    maximum_single_payout: Decimal | None = Field(default=None, alias="maximumSinglePayout")
    action_below_minimum: str = "block"
    updated_by: str = Field(default="api", alias="updatedBy")
    model_config = {"populate_by_name": True}


class BalanceRequest(BaseModel):
    confirmed_balance: Decimal = Field(alias="confirmedBalance")
    unconfirmed_balance: Decimal = Field(default=Decimal("0"), alias="unconfirmedBalance")
    locked_balance: Decimal = Field(default=Decimal("0"), alias="lockedBalance")
    available_balance: Decimal | None = Field(default=None, alias="availableBalance")
    block_height: int | None = Field(default=None, alias="blockHeight")
    source: str = "rpc"
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class HealthRequest(BaseModel):
    rpc_reachable: bool = Field(alias="rpcReachable")
    node_synced: bool = Field(alias="nodeSynced")
    wallet_unlocked: bool | None = Field(default=None, alias="walletUnlocked")
    spendable: bool
    address_valid: bool | None = Field(default=None, alias="addressValid")
    health_status: str | None = Field(default=None, alias="healthStatus")
    details: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class SelectionRequest(BaseModel):
    coin: str
    network: str
    assignment_scope: str = Field(alias="assignmentScope")
    scope_key: str = Field(default="*", alias="scopeKey")
    purpose: str
    amount: Decimal
    model_config = {"populate_by_name": True}


class ReconcileRequest(BaseModel):
    ledger_balance: Decimal = Field(alias="ledgerBalance")
    blockchain_balance: Decimal = Field(alias="blockchainBalance")
    tolerance: Decimal = Decimal("0.00000001")
    actor: str = "api"
    model_config = {"populate_by_name": True}


def call(method: str, **kwargs: Any) -> Any:
    try:
        return getattr(MultiWalletService(), method)(**kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Multi-wallet operation failed") from exc


@router.get("/coins")
def coins(enabled_only: bool = True):
    return call("coins", enabled_only=enabled_only)


@router.get("/coin-networks")
def networks(coin: str | None = None):
    return call("networks", coin=coin)


@router.put("/wallet-operations/assignments")
def assignment(request: AssignmentRequest):
    return call("assign", **request.model_dump())


@router.put("/wallet-operations/policies")
def policy(request: PolicyRequest):
    return call("policy", **request.model_dump())


@router.put("/wallet-operations/wallets/{wallet_id}/reserve")
def reserve(wallet_id: UUID, request: ReserveRequest):
    return call("reserve", wallet_id=wallet_id, **request.model_dump())


@router.post("/wallet-operations/wallets/{wallet_id}/balances")
def balance(wallet_id: UUID, request: BalanceRequest):
    return call("observe_balance", wallet_id=wallet_id, **request.model_dump())


@router.put("/wallet-operations/wallets/{wallet_id}/health")
def health(wallet_id: UUID, request: HealthRequest):
    return call("health", wallet_id=wallet_id, **request.model_dump())


@router.post("/wallet-operations/select")
def select(request: SelectionRequest):
    return call("select", **request.model_dump())


@router.post("/wallet-operations/wallets/{wallet_id}/reconcile")
def reconcile(wallet_id: UUID, request: ReconcileRequest):
    return call("reconcile", wallet_id=wallet_id, **request.model_dump())
