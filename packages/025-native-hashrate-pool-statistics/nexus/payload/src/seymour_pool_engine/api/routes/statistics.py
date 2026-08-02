from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query

from seymour_pool_engine.services.statistics_service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])
Window = Literal["1m", "5m", "15m", "1h"]


@router.get("/overview")
def overview(window: Annotated[Window, Query()] = "5m") -> dict:
    try:
        return StatisticsService().overview(window=window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Native statistics query failed") from exc


@router.get("/pools")
def pools(window: Annotated[Window, Query()] = "5m") -> dict:
    pool = overview(window)
    return {
        "source": pool["source"],
        "window": pool["window"],
        "windowSeconds": pool["windowSeconds"],
        "calculatedAt": pool["calculatedAt"],
        "count": 1,
        "pools": [pool],
    }


@router.get("/workers")
def workers(
    window: Annotated[Window, Query()] = "5m",
    limit: Annotated[int, Query(ge=1, le=5000)] = 100,
) -> dict:
    try:
        return StatisticsService().workers(window=window, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Worker statistics query failed") from exc


@router.get("/workers/{worker_name}")
def worker(worker_name: str, window: Annotated[Window, Query()] = "5m") -> dict:
    try:
        result = StatisticsService().worker(worker_name, window=window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Worker statistics query failed") from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    return result


@router.get("/engine")
def engine(window: Annotated[Window, Query()] = "5m") -> dict:
    try:
        return StatisticsService().engine(window=window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Engine statistics query failed") from exc
