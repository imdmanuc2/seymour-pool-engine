from decimal import Decimal

import pytest

from seymour_pool_engine.engines.jobs.models import StratumJob
from seymour_pool_engine.engines.shares.validator import (
    ShareValidationError,
    compact_to_target,
    difficulty_to_target,
    validate_share,
)


def job() -> StratumJob:
    return StratumJob(
        job_id="job1", template_height=1,
        previous_block_hash="00" * 32,
        coinbase1="02000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0b01012f5365796d6f75722f",
        coinbase2="ffffffff0100f2052a01000000015100000000",
        merkle_branches=(), version="20000000", nbits="1d00ffff", ntime="5e0ffff0",
        clean_jobs=True,
    )


def test_compact_target_matches_diff1() -> None:
    assert compact_to_target("1d00ffff") == difficulty_to_target(1)


def test_difficulty_target_scales() -> None:
    assert difficulty_to_target(2) == difficulty_to_target(1) // 2


def test_validate_well_formed_share() -> None:
    result = validate_share(
        job=job(),
        extranonce1="010203040506",
        extranonce2="00000001",
        submitted_ntime="5e0ffff0",
        nonce="00000000",
        difficulty=Decimal("0.0000000001"),
        extranonce2_size=4,
    )
    assert len(result.header_hex) == 160
    assert len(result.hash_hex) == 64
    assert result.accepted is True


def test_rejects_bad_extranonce_size() -> None:
    with pytest.raises(ShareValidationError) as exc:
        validate_share(job=job(), extranonce1="010203040506", extranonce2="01",
                       submitted_ntime="5e0ffff0", nonce="00000000", difficulty=1,
                       extranonce2_size=4)
    assert exc.value.reason == "malformed"


def test_rejects_old_ntime() -> None:
    with pytest.raises(ShareValidationError) as exc:
        validate_share(job=job(), extranonce1="010203040506", extranonce2="00000001",
                       submitted_ntime="5e0fffef", nonce="00000000", difficulty=1,
                       extranonce2_size=4)
    assert exc.value.reason == "invalid-time"
