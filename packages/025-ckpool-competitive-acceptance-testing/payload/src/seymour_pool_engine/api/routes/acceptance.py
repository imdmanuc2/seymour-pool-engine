from typing import Any

from fastapi import APIRouter, Query

from seymour_pool_engine.repositories.acceptance_repository import AcceptanceRepository
from seymour_pool_engine.services.acceptance_service import AcceptanceService

router = APIRouter(prefix="/acceptance", tags=["acceptance"])


@router.post("/run")
def run(
    profile: str = Query(default="release", min_length=1, max_length=40),
) -> dict[str, Any]:
    return AcceptanceService().run(profile=profile, persist=True)


@router.get("/runs")
def runs(limit: int = Query(default=25, ge=1, le=250)) -> list[dict[str, Any]]:
    return AcceptanceRepository().recent(limit)


@router.get("/criteria")
def criteria() -> dict[str, Any]:
    return {
        "release": "All automated checks pass; no missing critical API contracts.",
        "soak": "Run external multi-miner and failover harness for the planned duration.",
        "comparison": (
            "Record Seymour and CKPool results on identical hardware and node configuration."
        ),
    }
