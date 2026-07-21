from typing import Any

from fastapi import APIRouter, Query

from seymour_pool_engine.services.stratum_service import StratumService

router = APIRouter(prefix="/stratum", tags=["stratum"])


@router.get("/status")
def status() -> dict[str, Any]:
    return StratumService().status()


@router.get("/sessions")
def sessions(limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, Any]]:
    return StratumService().sessions(limit)
