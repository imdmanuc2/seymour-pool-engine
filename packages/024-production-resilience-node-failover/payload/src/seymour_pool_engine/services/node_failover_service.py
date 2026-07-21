from __future__ import annotations

from typing import Any

from seymour_pool_engine.providers.bitcoin.factory import create_bitcoin_rpc_client
from seymour_pool_engine.providers.bitcoin.resilience import ResilientBitcoinRpcClient
from seymour_pool_engine.repositories.node_failover_repository import NodeFailoverRepository


class NodeFailoverService:
    def __init__(
        self,
        rpc: ResilientBitcoinRpcClient | None = None,
        repository: NodeFailoverRepository | None = None,
    ) -> None:
        self.rpc = rpc or create_bitcoin_rpc_client()
        self.repository = repository or NodeFailoverRepository()

    def status(self) -> dict[str, Any]:
        return self.rpc.status()

    def probe(self) -> dict[str, Any]:
        before = self.rpc.url
        result = self.rpc.probe()
        after = self.rpc.url
        event_type = "probe_ok" if before == after else "failover"
        try:
            self.repository.record(endpoint=after, event_type=event_type, detail=f"from={before}")
        except Exception:
            result["historyPersistence"] = "unavailable"
        return result

    def history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.history(limit)
