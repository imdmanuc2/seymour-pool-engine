from abc import ABC, abstractmethod

from seymour_pool_engine.providers.models import PoolSummary, ProviderStatus, WorkerSummary


class MiningProvider(ABC):
    """Stable contract implemented by mining backends."""

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        raise NotImplementedError

    @abstractmethod
    def list_pools(self) -> list[PoolSummary]:
        raise NotImplementedError

    @abstractmethod
    def list_workers(self, pool_id: str | None = None) -> list[WorkerSummary]:
        raise NotImplementedError
