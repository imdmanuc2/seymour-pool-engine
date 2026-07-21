from typing import Any

from fastapi import APIRouter, Query

from seymour_pool_engine.services.node_failover_service import NodeFailoverService

router = APIRouter(prefix="/bitcoin/nodes", tags=["bitcoin-node-failover"])


@router.get("/status")
def status() -> dict[str, Any]:
    return NodeFailoverService().status()


@router.post("/probe")
def probe() -> dict[str, Any]:
    return NodeFailoverService().probe()


@router.get("/failover-history")
def history(limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, Any]]:
    return NodeFailoverService().history(limit)
