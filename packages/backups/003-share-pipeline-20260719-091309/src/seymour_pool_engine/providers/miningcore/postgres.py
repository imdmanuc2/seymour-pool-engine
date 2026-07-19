from typing import Any

from seymour_pool_engine.database import miningcore_connection

EXPECTED_TABLES = {
    "balance_changes",
    "balances",
    "blocks",
    "miner_settings",
    "minerstats",
    "payments",
    "poolstats",
    "shares",
}


class MiningCorePostgresClient:
    def discover_schema(self) -> dict[str, Any]:
        with miningcore_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
            tables = {row["table_name"] for row in cursor.fetchall()}
        missing = sorted(EXPECTED_TABLES - tables)
        return {
            "tables": sorted(tables),
            "missingTables": missing,
            "compatible": not missing,
        }

    def latest_pool_stats(self) -> list[dict[str, Any]]:
        with miningcore_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT ON (poolid)
                    poolid, connectedminers, poolhashrate, sharespersecond,
                    networkhashrate, networkdifficulty, blockheight,
                    connectedpeers, created
                FROM public.poolstats
                ORDER BY poolid, created DESC
                """
            )
            return list(cursor.fetchall())

    def latest_worker_stats(self, pool_id: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT DISTINCT ON (poolid, miner, worker)
                poolid, miner, worker, hashrate, sharespersecond, created
            FROM public.minerstats
        """
        params: tuple[str, ...] = ()
        if pool_id:
            query += " WHERE poolid = %s"
            params = (pool_id,)
        query += " ORDER BY poolid, miner, worker, created DESC"
        with miningcore_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
            return list(cursor.fetchall())
