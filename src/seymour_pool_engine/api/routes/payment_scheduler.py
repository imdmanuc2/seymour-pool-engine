from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from seymour_pool_engine.services.payment_scheduler_service import PaymentSchedulerService

router = APIRouter(tags=["payment-scheduler"])


class SchedulerProfileRequest(BaseModel):
    pool_id: str = Field(alias="poolId")
    coin: str
    network: str
    source_wallet_id: UUID = Field(alias="sourceWalletId")
    enabled: bool = True
    schedule_type: str = Field(default="daily", alias="scheduleType")
    schedule_hour: int | None = Field(default=None, alias="scheduleHour")
    schedule_weekday: int | None = Field(default=None, alias="scheduleWeekday")
    schedule_monthday: int | None = Field(default=None, alias="scheduleMonthday")
    minimum_payout: str = Field(alias="minimumPayout")
    absolute_minimum: str = Field(default="0", alias="absoluteMinimum")
    maximum_payout: str | None = Field(default=None, alias="maximumPayout")
    maximum_behavior: str = Field(default="pay_full", alias="maximumBehavior")
    retry_limit: int = Field(default=3, alias="retryLimit")
    retry_backoff_seconds: int = Field(default=300, alias="retryBackoffSeconds")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class WorkerPaymentPolicyRequest(BaseModel):
    worker_id: UUID = Field(alias="workerId")
    coin: str
    network: str
    enabled: bool = True
    minimum_payout: str | None = Field(default=None, alias="minimumPayout")
    schedule_type: str | None = Field(default=None, alias="scheduleType")
    destination_wallet_id: UUID | None = Field(default=None, alias="destinationWalletId")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class ActorRequest(BaseModel):
    actor: str = "api"


@router.get("/payment-scheduler/profiles")
def list_profiles(pool_id: str | None = None) -> list[dict[str, Any]]:
    return PaymentSchedulerService().profiles(pool_id=pool_id)


@router.put("/payment-scheduler/profiles")
def configure_profile(request: SchedulerProfileRequest) -> dict[str, Any]:
    try:
        return PaymentSchedulerService().configure_profile(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/payment-scheduler/worker-policies")
def configure_worker_policy(request: WorkerPaymentPolicyRequest) -> dict[str, Any]:
    try:
        return PaymentSchedulerService().configure_worker_policy(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/payment-scheduler/run-due")
def run_due(request: ActorRequest) -> list[dict[str, Any]]:
    try:
        return PaymentSchedulerService().run_due(actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/payment-scheduler/profiles/{scheduler_profile_id}/run")
def run_profile(
    scheduler_profile_id: UUID, request: ActorRequest
) -> dict[str, Any]:
    try:
        return PaymentSchedulerService().run_profile(
            scheduler_profile_id=scheduler_profile_id, actor=request.actor
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/payment-scheduler/runs")
def list_runs(
    scheduler_profile_id: UUID | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    return PaymentSchedulerService().runs(
        scheduler_profile_id=scheduler_profile_id, limit=limit
    )


@router.get("/payment-scheduler/jobs")
def list_jobs(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    return PaymentSchedulerService().jobs(status=status, limit=limit)


@router.post("/payment-scheduler/jobs/{scheduler_job_id}/retry")
def retry_job(scheduler_job_id: UUID) -> dict[str, Any]:
    try:
        return PaymentSchedulerService().retry_job(scheduler_job_id=scheduler_job_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/payment-scheduler/jobs/{scheduler_job_id}/cancel")
def cancel_job(scheduler_job_id: UUID) -> dict[str, Any]:
    try:
        return PaymentSchedulerService().cancel_job(scheduler_job_id=scheduler_job_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
