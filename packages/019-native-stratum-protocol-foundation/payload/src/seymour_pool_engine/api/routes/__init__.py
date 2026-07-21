from seymour_pool_engine.api.routes.blocks import router as blocks_router
from seymour_pool_engine.api.routes.coinbase_maturity import (
    router as coinbase_maturity_router,
)
from seymour_pool_engine.api.routes.configuration import router as configuration_router
from seymour_pool_engine.api.routes.diagnostics import router as diagnostics_router
from seymour_pool_engine.api.routes.economics import router as economics_router
from seymour_pool_engine.api.routes.health import router as health_router
from seymour_pool_engine.api.routes.integration import router as integration_router
from seymour_pool_engine.api.routes.miningcore import router as miningcore_router
from seymour_pool_engine.api.routes.monitoring import router as monitoring_router
from seymour_pool_engine.api.routes.multi_wallets import router as multi_wallets_router
from seymour_pool_engine.api.routes.payment_scheduler import (
    router as payment_scheduler_router,
)
from seymour_pool_engine.api.routes.payouts import router as payouts_router
from seymour_pool_engine.api.routes.reliability import router as reliability_router  # noqa: F401
from seymour_pool_engine.api.routes.rewards import router as rewards_router
from seymour_pool_engine.api.routes.security import router as security_router
from seymour_pool_engine.api.routes.shares import router as shares_router
from seymour_pool_engine.api.routes.statistics import router as statistics_router
from seymour_pool_engine.api.routes.stratum import router as stratum_router
from seymour_pool_engine.api.routes.system import router as system_router
from seymour_pool_engine.api.routes.wallets import router as wallets_router
from seymour_pool_engine.api.routes.workers import router as workers_router

__all__ = [
    "blocks_router",
    "coinbase_maturity_router",
    "configuration_router",
    "health_router",
    "integration_router",
    "diagnostics_router",
    "economics_router",
    "miningcore_router",
    "monitoring_router",
    "multi_wallets_router",
    "payment_scheduler_router",
    "payouts_router",
    "rewards_router",
    "security_router",
    "shares_router",
    "statistics_router",
    "stratum_router",
    "system_router",
    "workers_router",
    "wallets_router",
]
