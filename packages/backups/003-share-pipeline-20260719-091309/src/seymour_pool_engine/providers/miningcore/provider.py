from datetime import UTC, datetime

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.providers.base import MiningProvider
from seymour_pool_engine.providers.miningcore.postgres import MiningCorePostgresClient
from seymour_pool_engine.providers.miningcore.rest import MiningCoreRestClient
from seymour_pool_engine.providers.models import (
    ComponentCheck,
    PoolSummary,
    ProviderStatus,
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
