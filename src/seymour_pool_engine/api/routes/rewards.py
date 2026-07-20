from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from seymour_pool_engine.services.reward_service import (
    calculate_rewards,
    confirm_rewards,
    get_balances,
    get_reward_periods,
)

router = APIRouter(prefix="/rewards", tags=["rewards"])


class RewardCalculationRequest(BaseModel):
    block_id: UUID = Field(alias="blockId")
    pool_id: str = Field(alias="poolId")
    gross_reward: Decimal = Field(alias="grossReward")
    fee_percent: Decimal = Field(default=Decimal("0"), alias="feePercent")
    start_at: datetime = Field(alias="startAt")
    end_at: datetime = Field(alias="endAt")

    model_config = {"populate_by_name": True}


@router.get("")
def reward_periods(
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
    limit: Annotated[int, Query()] = 100,
) -> dict:
    try:
        return get_reward_periods(pool_id=pool_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Reward period query failed") from exc


@router.get("/balances")
def balances(
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
    miner: Annotated[str | None, Query()] = None,
) -> dict:
    try:
        return get_balances(pool_id=pool_id, miner=miner)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Balance query failed") from exc


@router.post("/calculate")
def calculate(request: RewardCalculationRequest) -> dict:
    try:
        return calculate_rewards(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Reward calculation failed") from exc


@router.post("/{reward_period_id}/confirm")
def confirm(reward_period_id: UUID) -> dict:
    try:
        return confirm_rewards(reward_period_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Reward confirmation failed") from exc
