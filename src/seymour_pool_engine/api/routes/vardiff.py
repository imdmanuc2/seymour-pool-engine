from typing import Any

from fastapi import APIRouter, Query

from seymour_pool_engine.services.vardiff_service import VarDiffService

router = APIRouter(prefix="/vardiff", tags=["vardiff"])


@router.get("/status")
def status() -> dict[str, Any]:
    return VarDiffService().status()


@router.get("/history")
def history(limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, Any]]:
    return VarDiffService().history(limit)
