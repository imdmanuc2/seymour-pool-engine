from datetime import UTC, datetime
from hashlib import sha256

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.providers.base import MiningProvider
from seymour_pool_engine.providers.miningcore.postgres import MiningCorePostgresClient
from seymour_pool_engine.providers.miningcore.rest import MiningCoreRestClient
from seymour_pool_engine.providers.models import (
    ComponentCheck,
    PoolSummary,
    ProviderStatus,
    ShareSummary,
    WorkerSummary,
)


class MiningCoreProvider(MiningProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.rest = MiningCoreRestClient(settings.miningcore_api_url)
        self.postgres = MiningCorePostgresClient()

    def get_status(self) -> ProviderStatus:
        rest_result = self.rest.health()
        checks = [ComponentCheck(component="miningcore-rest", **rest_result)]
        capabilities: list[str] = []
        schema_compatible = False

        if not self.settings.miningcore_database_url:
            checks.append(
                ComponentCheck(
                    component="miningcore-database",
                    status="disabled",
                    summary="MiningCore PostgreSQL connector is not configured",
                )
            )
        else:
            try:
                schema = self.postgres.discover_schema()
                schema_compatible = bool(schema["compatible"])
                capabilities = schema["tables"]
                checks.append(
                    ComponentCheck(
                        component="miningcore-database",
                        status="online" if schema_compatible else "degraded",
                        summary=(
                            "MiningCore schema is compatible"
                            if schema_compatible
                            else "MiningCore schema is missing expected tables"
                        ),
                        details=schema,
                    )
                )
            except Exception as exc:
                checks.append(
                    ComponentCheck(
                        component="miningcore-database",
                        status="offline",
                        summary="MiningCore PostgreSQL connection failed",
                        details={"error": str(exc)},
                    )
                )

        statuses = {check.status for check in checks}
        status = "online"
        if "offline" in statuses:
            status = "degraded" if "online" in statuses else "offline"
        elif "degraded" in statuses:
            status = "degraded"
        elif statuses == {"disabled"}:
            status = "disabled"

        return ProviderStatus(
            provider="miningcore",
            status=status,
            observedAt=datetime.now(UTC),
            schemaCompatible=schema_compatible,
            capabilities=capabilities,
            checks=checks,
        )

    def list_pools(self) -> list[PoolSummary]:
        return [
            PoolSummary(
                poolId=row["poolid"],
                connectedMiners=row["connectedminers"],
                poolHashrate=row["poolhashrate"],
                sharesPerSecond=row["sharespersecond"],
                networkHashrate=row["networkhashrate"],
                networkDifficulty=row["networkdifficulty"],
                blockHeight=row["blockheight"],
                connectedPeers=row["connectedpeers"],
                observedAt=row["created"],
            )
            for row in self.postgres.latest_pool_stats()
        ]

    def list_workers(self, pool_id: str | None = None) -> list[WorkerSummary]:
        return [
            WorkerSummary(
                poolId=row["poolid"],
                miner=row["miner"],
                worker=row["worker"],
                hashrate=row["hashrate"],
                sharesPerSecond=row["sharespersecond"],
                observedAt=row["created"],
            )
            for row in self.postgres.latest_worker_stats(pool_id)
        ]

    def list_shares(
        self,
        *,
        pool_id: str | None = None,
        since: datetime | None = None,
        limit: int = 1000,
    ) -> list[ShareSummary]:
        shares: list[ShareSummary] = []
        for row in self.postgres.latest_shares(pool_id=pool_id, since=since, limit=limit):
            key_material = "|".join(
                [
                    str(row["poolid"]),
                    str(row["miner"]),
                    str(row.get("worker") or ""),
                    str(row["difficulty"]),
                    str(row.get("networkdifficulty")),
                    str(row.get("blockheight")),
                    str(row.get("ipaddress")),
                    str(row.get("useragent")),
                    row["created"].isoformat(),
                ]
            )
            shares.append(
                ShareSummary(
                    providerShareKey=sha256(key_material.encode("utf-8")).hexdigest(),
                    poolId=row["poolid"],
                    miner=row["miner"],
                    worker=row.get("worker") or "",
                    difficulty=row["difficulty"],
                    networkDifficulty=row.get("networkdifficulty"),
                    blockHeight=row.get("blockheight"),
                    ipAddress=row.get("ipaddress"),
                    userAgent=row.get("useragent"),
                    createdAt=row["created"],
                )
            )
        return shares
