from typing import Any

from seymour_pool_engine.repositories.stratum_repository import StratumRepository


class StratumService:
    def __init__(self) -> None:
        self.repository = StratumRepository()

    def status(self) -> dict[str, Any]:
        return {
            "service": "seymour-native-stratum",
            "protocol": "stratum-v1",
            "jobSource": "synthetic-package-019",
            **self.repository.status(),
        }

    def sessions(self, limit: int) -> list[dict[str, Any]]:
        return self.repository.sessions(limit)
