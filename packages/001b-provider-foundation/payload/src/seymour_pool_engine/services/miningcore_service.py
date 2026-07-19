from seymour_pool_engine.providers.miningcore import MiningCoreProvider


def get_miningcore_status() -> dict:
    return MiningCoreProvider().get_status().model_dump(by_alias=True, mode="json")


def get_miningcore_pools() -> dict:
    pools = MiningCoreProvider().list_pools()
    return {"count": len(pools), "pools": [p.model_dump(by_alias=True, mode="json") for p in pools]}


def get_miningcore_workers(pool_id: str | None = None) -> dict:
    workers = MiningCoreProvider().list_workers(pool_id)
    return {
        "count": len(workers),
        "poolId": pool_id,
        "workers": [w.model_dump(by_alias=True, mode="json") for w in workers],
    }
