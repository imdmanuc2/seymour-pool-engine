from fastapi import APIRouter

from seymour_pool_engine.api.routes import (
    blocks_router,
    diagnostics_router,
    economics_router,
    health_router,
    miningcore_router,
    monitoring_router,
    rewards_router,
    shares_router,
    statistics_router,
    system_router,
    workers_router,
)

api_router = APIRouter()
api_router.include_router(blocks_router)
api_router.include_router(diagnostics_router)
api_router.include_router(economics_router)
api_router.include_router(system_router)
api_router.include_router(health_router)
api_router.include_router(miningcore_router)
api_router.include_router(monitoring_router)
api_router.include_router(rewards_router)
api_router.include_router(workers_router)
api_router.include_router(shares_router)
api_router.include_router(statistics_router)
