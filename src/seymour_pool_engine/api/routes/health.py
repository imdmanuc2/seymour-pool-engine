from fastapi import APIRouter
from fastapi.responses import JSONResponse

from seymour_pool_engine.services import get_health

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> JSONResponse:
    result = get_health()
    status_code = 200 if result["status"] == "online" else 503
    return JSONResponse(content=result, status_code=status_code)
