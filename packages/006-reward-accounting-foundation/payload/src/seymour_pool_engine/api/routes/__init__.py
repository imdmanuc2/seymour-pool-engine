from seymour_pool_engine.api.routes.blocks import router as blocks_router
from seymour_pool_engine.api.routes.health import router as health_router
from seymour_pool_engine.api.routes.miningcore import router as miningcore_router
from seymour_pool_engine.api.routes.rewards import router as rewards_router
from seymour_pool_engine.api.routes.shares import router as shares_router
from seymour_pool_engine.api.routes.statistics import router as statistics_router
from seymour_pool_engine.api.routes.system import router as system_router
from seymour_pool_engine.api.routes.workers import router as workers_router

__all__ = [
    "blocks_router",
    "health_router",
    "miningcore_router",
    "rewards_router",
    "shares_router",
    "statistics_router",
    "system_router",
    "workers_router",
]
