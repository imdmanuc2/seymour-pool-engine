from __future__ import annotations

from typing import Protocol

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.engines.jobs.bitcoin import create_stratum_job
from seymour_pool_engine.engines.jobs.models import BitcoinBlockTemplate, StratumJob
from seymour_pool_engine.providers.bitcoin import BitcoinRpcClient
from seymour_pool_engine.repositories.stratum_repository import StratumRepository


class TemplateProvider(Protocol):
    def get_block_template(self) -> dict: ...


class TemplateJobService:
    def __init__(
        self,
        provider: TemplateProvider | None = None,
        repository: StratumRepository | None = None,
    ) -> None:
        settings = get_settings()
        self.settings = settings
        self.provider = provider or BitcoinRpcClient(
            settings.bitcoin_rpc_url,
            settings.bitcoin_rpc_user,
            settings.bitcoin_rpc_password,
            settings.bitcoin_rpc_timeout_seconds,
        )
        self.repository = repository or StratumRepository()

    def refresh(self, clean_jobs: bool = True) -> StratumJob:
        template = BitcoinBlockTemplate.from_rpc(self.provider.get_block_template())
        job = create_stratum_job(
            template,
            self.settings.bitcoin_payout_script,
            extranonce1_size=self.settings.stratum_extranonce1_size,
            extranonce2_size=self.settings.stratum_extranonce2_size,
            clean_jobs=clean_jobs,
            coinbase_tag=self.settings.bitcoin_coinbase_tag,
        )
        self.repository.record_template(template)
        self.repository.record_job(job)
        return job

    def latest(self) -> StratumJob | None:
        return self.repository.latest_job()

    def status(self) -> dict:
        return self.repository.template_status()
