from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from seymour_pool_engine.services.economics_service import EconomicsService

router = APIRouter(prefix="/economics", tags=["economics"])


class FeeProfileRequest(BaseModel):
    pool_id: str = Field(alias="poolId")
    coin: str
    developer_fee_percent: Decimal = Field(default=Decimal("0.75"), alias="developerFeePercent")
    developer_destination: str = Field(alias="developerDestination")
    operator_fee_percent: Decimal = Field(default=Decimal("0"), alias="operatorFeePercent")
    operator_destination: str | None = Field(default=None, alias="operatorDestination")
    model_config = {"populate_by_name": True}


class WorkerWeight(BaseModel):
    recipient_key: str = Field(alias="recipientKey")
    weight: Decimal
    model_config = {"populate_by_name": True}


class EconomicsCalculationRequest(BaseModel):
    block_id: UUID = Field(alias="blockId")
    pool_id: str = Field(alias="poolId")
    coin: str
    policy: str
    gross_reward: Decimal = Field(alias="grossReward")
    worker_weights: list[WorkerWeight] = Field(alias="workerWeights")
    model_config = {"populate_by_name": True}


@router.put("/fees")
def configure_fees(request: FeeProfileRequest) -> dict[str, Any]:
    try:
        return EconomicsService().configure_fee_profile(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Fee profile update failed") from exc


@router.post("/calculations")
def calculate(request: EconomicsCalculationRequest) -> dict[str, Any]:
    try:
        values=request.model_dump()
        values["worker_weights"]=[{"recipientKey": x["recipient_key"], "weight": x["weight"]} for x in values["worker_weights"]]
        return EconomicsService().calculate(**values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Economics calculation failed") from exc


@router.get("/summary")
def summary(pool_id: Annotated[str | None, Query(alias="poolId")]=None,
            coin: Annotated[str | None, Query()]=None) -> dict[str, Any]:
    try:
        return EconomicsService().summary(pool_id=pool_id, coin=coin)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Economics summary failed") from exc


@router.get("/policy")
def policy() -> dict[str, Any]:
    return {"developerFeeRequired": True, "minimumDeveloperFeePercent": 0.75,
            "operatorMayIncreaseDeveloperFee": True, "operatorMayDisableDeveloperFee": False,
            "supportedRewardPolicies": ["solo", "prop", "pplns"],
            "transparency": "All fee destinations and allocations are visible and auditable."}
