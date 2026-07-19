from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from seymour_pool_engine.services.share_service import get_shares, synchronize_shares

router = APIRouter(prefix="/shares", tags=["shares"])


@router.get("")
def shares(
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
    miner: Annotated[str | None, Query()] = None,
    worker: Annotated[str | None, Query()] = None,
    provider: Annotated[str | None, Query()] = None,
    since: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query()] = 100,
) -> dict:
    try:
        return get_shares(
            pool_id=pool_id,
            miner=miner,
            worker=worker,
            provider_name=provider,
            since=since,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Share inventory query failed") from exc


@router.post("/sync")
def sync_shares(
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
    since: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query()] = 1000,
) -> dict:
    try:
        return synchronize_shares(pool_id=pool_id, since=since, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Share provider synchronization failed",
        ) from exc
