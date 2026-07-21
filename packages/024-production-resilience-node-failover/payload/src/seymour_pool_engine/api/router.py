from fastapi import APIRouter

from seymour_pool_engine.api.routes import (
    block_candidates_router,
    blocks_router,
    coinbase_maturity_router,
    configuration_router,
    diagnostics_router,
    economics_router,
    health_router,
    integration_router,
    miningcore_router,
    monitoring_router,
    multi_wallets_router,
    node_failover_router,
    payment_scheduler_router,
    payouts_router,
    reliability_router,
    rewards_router,
    security_router,
    shares_router,
    statistics_router,
    stratum_router,
    system_router,
    templates_router,
    vardiff_router,
    wallets_router,
    workers_router,
)

api_router = APIRouter()
api_router.include_router(block_candidates_router)
api_router.include_router(blocks_router)
api_router.include_router(coinbase_maturity_router)
api_router.include_router(configuration_router)
api_router.include_router(diagnostics_router)
api_router.include_router(economics_router)
api_router.include_router(system_router)
api_router.include_router(health_router)
api_router.include_router(integration_router)
api_router.include_router(miningcore_router)
api_router.include_router(monitoring_router)
api_router.include_router(node_failover_router)
api_router.include_router(multi_wallets_router)
api_router.include_router(payment_scheduler_router)
api_router.include_router(payouts_router)
api_router.include_router(reliability_router)
api_router.include_router(rewards_router)
api_router.include_router(security_router)
api_router.include_router(wallets_router)
api_router.include_router(workers_router)
api_router.include_router(shares_router)
api_router.include_router(statistics_router)
api_router.include_router(stratum_router)
api_router.include_router(templates_router)
api_router.include_router(vardiff_router)
