from __future__ import annotations

from dataclasses import dataclass

from seymour_pool_engine.config.settings import get_settings
from seymour_pool_engine.engines.blocks.builder import AssembledBlock, assemble_block
from seymour_pool_engine.engines.jobs.models import BitcoinBlockTemplate, StratumJob
from seymour_pool_engine.engines.shares.validator import ShareValidationResult
from seymour_pool_engine.providers.bitcoin.rpc import BitcoinRpcClient, BitcoinRpcError
from seymour_pool_engine.repositories.block_candidate_repository import BlockCandidateRepository


@dataclass(frozen=True, slots=True)
class BlockSubmissionResult:
    candidate_id: str
    accepted: bool
    block: AssembledBlock
    rpc_result: str | None
    error: str | None


class BlockSubmissionService:
    def __init__(
        self,
        repository: BlockCandidateRepository | None = None,
        rpc: BitcoinRpcClient | None = None,
    ) -> None:
        settings = get_settings()
        self.repository = repository or BlockCandidateRepository()
        self.rpc = rpc or BitcoinRpcClient(
            settings.bitcoin_rpc_url,
            settings.bitcoin_rpc_user,
            settings.bitcoin_rpc_password,
            settings.bitcoin_rpc_timeout_seconds,
        )

    def submit_candidate(
        self,
        *,
        job: StratumJob,
        template: BitcoinBlockTemplate,
        validation: ShareValidationResult,
        extranonce1: str,
        extranonce2: str,
    ) -> BlockSubmissionResult:
        block = assemble_block(
            job=job,
            template=template,
            validation=validation,
            extranonce1=extranonce1,
            extranonce2=extranonce2,
        )
        candidate_id = self.repository.create(block=block, job=job, work_id=template.work_id)
        try:
            rpc_result = self.rpc.submit_block(block.block_hex, template.work_id)
            accepted = rpc_result is None
            error = None if accepted else rpc_result
        except BitcoinRpcError as exc:
            rpc_result = None
            accepted = False
            error = str(exc)
        self.repository.mark_submitted(
            candidate_id, accepted=accepted, result=rpc_result, error=error
        )
        return BlockSubmissionResult(candidate_id, accepted, block, rpc_result, error)
