from __future__ import annotations

from dataclasses import dataclass

from seymour_pool_engine.engines.blocks.builder import AssembledBlock, assemble_block
from seymour_pool_engine.engines.jobs.models import BitcoinBlockTemplate, StratumJob
from seymour_pool_engine.engines.shares.validator import ShareValidationResult
from seymour_pool_engine.providers.bitcoin import BitcoinRpcError, create_bitcoin_rpc_client
from seymour_pool_engine.providers.bitcoin.resilience import ResilientBitcoinRpcClient
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
        rpc: ResilientBitcoinRpcClient | None = None,
    ) -> None:
        self.repository = repository or BlockCandidateRepository()
        self.rpc = rpc or create_bitcoin_rpc_client()

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
