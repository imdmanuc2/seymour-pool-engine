from typing import Any

from seymour_pool_engine.engines.vardiff import VarDiffConfig
from seymour_pool_engine.repositories.stratum_repository import StratumRepository


class VarDiffService:
    def __init__(self, repository: StratumRepository | None = None) -> None:
        self.repository = repository or StratumRepository()
        self.config = VarDiffConfig()

    def status(self) -> dict[str, Any]:
        return {
            "service": "seymour-vardiff",
            "enabled": True,
            "targetShareSeconds": self.config.target_share_seconds,
            "retargetIntervalSeconds": self.config.retarget_interval_seconds,
            "minimumDifficulty": self.config.min_difficulty,
            "maximumDifficulty": self.config.max_difficulty,
            "variancePercent": self.config.variance_percent,
            **self.repository.vardiff_status(),
        }

    def history(self, limit: int) -> list[dict[str, Any]]:
        return self.repository.difficulty_history(limit)
