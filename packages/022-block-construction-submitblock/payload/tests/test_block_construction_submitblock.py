from decimal import Decimal

from seymour_pool_engine.engines.blocks.builder import assemble_block, encode_varint
from seymour_pool_engine.engines.jobs.models import (
    BitcoinBlockTemplate,
    BitcoinTransaction,
    StratumJob,
)
from seymour_pool_engine.engines.shares.validator import ShareValidationResult
from seymour_pool_engine.services.block_submission_service import BlockSubmissionService


def job() -> StratumJob:
    return StratumJob(
        "j1",
        100,
        "00" * 32,
        "0100000001" + "00" * 32 + "ffffffff01",
        "00",
        (),
        "20000000",
        "1d00ffff",
        "6a5f75e0",
        True,
    )


def template() -> BitcoinBlockTemplate:
    return BitcoinBlockTemplate(
        100,
        "00" * 32,
        0x20000000,
        "1d00ffff",
        1,
        1,
        5_000_000_000,
        (BitcoinTransaction("11" * 32, "11" * 32, "01000000000000000000"),),
        work_id="w1",
    )


def validation() -> ShareValidationResult:
    return ShareValidationResult(
        True, True, "22" * 32, 1, 2, 3, Decimal("1"), "33" * 32, "44" * 32, "00" * 80
    )


def test_varint_boundaries() -> None:
    assert encode_varint(252) == b"\xfc"
    assert encode_varint(253) == b"\xfd\xfd\x00"
    assert encode_varint(65536) == b"\xfe\x00\x00\x01\x00"


def test_assemble_block_includes_header_count_coinbase_and_transactions() -> None:
    block = assemble_block(
        job=job(), template=template(), validation=validation(), extranonce1="aa", extranonce2="bb"
    )
    assert block.block_hex.startswith("00" * 80 + "02")
    assert block.transaction_count == 2
    assert block.block_hash == "22" * 32


class Repo:
    def __init__(self) -> None:
        self.marked = None

    def create(self, **kwargs):
        return "candidate-1"

    def mark_submitted(self, candidate_id, **kwargs):
        self.marked = (candidate_id, kwargs)


class Rpc:
    def __init__(self, result=None):
        self.result = result

    def submit_block(self, block_hex, work_id=None):
        assert block_hex
        assert work_id == "w1"
        return self.result


def test_submission_acceptance() -> None:
    repo = Repo()
    result = BlockSubmissionService(repository=repo, rpc=Rpc()).submit_candidate(
        job=job(), template=template(), validation=validation(), extranonce1="aa", extranonce2="bb"
    )
    assert result.accepted is True
    assert repo.marked[1]["accepted"] is True


def test_submission_rejection_string() -> None:
    repo = Repo()
    result = BlockSubmissionService(repository=repo, rpc=Rpc("high-hash")).submit_candidate(
        job=job(), template=template(), validation=validation(), extranonce1="aa", extranonce2="bb"
    )
    assert result.accepted is False
    assert result.error == "high-hash"
