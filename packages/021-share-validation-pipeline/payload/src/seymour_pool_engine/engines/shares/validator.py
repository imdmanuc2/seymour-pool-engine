from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext

from seymour_pool_engine.engines.jobs.models import StratumJob

DIFF1_TARGET = 0x00FFFF << (8 * (0x1D - 3))


class ShareValidationError(ValueError):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


@dataclass(frozen=True, slots=True)
class ShareValidationResult:
    accepted: bool
    block_candidate: bool
    hash_hex: str
    hash_value: int
    share_target: int
    network_target: int
    achieved_difficulty: Decimal
    coinbase_hash: str
    merkle_root: str
    header_hex: str


def _double_sha256(value: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(value).digest()).digest()


def _hex_bytes(value: str, *, name: str, exact_bytes: int | None = None) -> bytes:
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise ShareValidationError("malformed", f"{name} must be hexadecimal") from exc
    if exact_bytes is not None and len(decoded) != exact_bytes:
        raise ShareValidationError("malformed", f"{name} must be {exact_bytes} bytes")
    return decoded


def compact_to_target(bits: str) -> int:
    raw = _hex_bytes(bits, name="nbits", exact_bytes=4)
    compact = int.from_bytes(raw, "big")
    exponent = compact >> 24
    coefficient = compact & 0x007FFFFF
    if compact & 0x00800000 or coefficient == 0:
        raise ShareValidationError("invalid-job", "job contains invalid compact target")
    if exponent <= 3:
        return coefficient >> (8 * (3 - exponent))
    return coefficient << (8 * (exponent - 3))


def difficulty_to_target(difficulty: float | Decimal) -> int:
    try:
        normalized = Decimal(str(difficulty))
    except InvalidOperation as exc:
        raise ShareValidationError("invalid-difficulty", "share difficulty is invalid") from exc
    if normalized <= 0:
        raise ShareValidationError("invalid-difficulty", "share difficulty must be positive")
    with localcontext() as context:
        context.prec = 100
        return int(Decimal(DIFF1_TARGET) / normalized)


def validate_share(
    *,
    job: StratumJob,
    extranonce1: str,
    extranonce2: str,
    submitted_ntime: str,
    nonce: str,
    difficulty: float | Decimal,
    extranonce2_size: int,
) -> ShareValidationResult:
    _hex_bytes(extranonce1, name="extranonce1")
    _hex_bytes(extranonce2, name="extranonce2", exact_bytes=extranonce2_size)
    ntime = _hex_bytes(submitted_ntime, name="ntime", exact_bytes=4)
    nonce_bytes = _hex_bytes(nonce, name="nonce", exact_bytes=4)
    if int(submitted_ntime, 16) < int(job.ntime, 16):
        raise ShareValidationError("invalid-time", "submitted ntime predates the job")

    coinbase_hex = job.coinbase1 + extranonce1 + extranonce2 + job.coinbase2
    coinbase = _hex_bytes(coinbase_hex, name="coinbase")
    coinbase_hash = _double_sha256(coinbase)
    merkle_root = coinbase_hash
    for branch_hex in job.merkle_branches:
        branch = _hex_bytes(branch_hex, name="merkle branch", exact_bytes=32)[::-1]
        merkle_root = _double_sha256(merkle_root + branch)

    version = _hex_bytes(job.version, name="version", exact_bytes=4)[::-1]
    previous = _hex_bytes(job.previous_block_hash, name="previous block hash", exact_bytes=32)[::-1]
    bits = _hex_bytes(job.nbits, name="nbits", exact_bytes=4)[::-1]
    header = version + previous + merkle_root + ntime[::-1] + bits + nonce_bytes[::-1]
    digest = _double_sha256(header)
    hash_value = int.from_bytes(digest, "little")
    share_target = difficulty_to_target(difficulty)
    network_target = compact_to_target(job.nbits)
    with localcontext() as context:
        context.prec = 100
        achieved = Decimal(DIFF1_TARGET) / Decimal(max(hash_value, 1))
    return ShareValidationResult(
        accepted=hash_value <= share_target,
        block_candidate=hash_value <= network_target,
        hash_hex=digest[::-1].hex(),
        hash_value=hash_value,
        share_target=share_target,
        network_target=network_target,
        achieved_difficulty=achieved,
        coinbase_hash=coinbase_hash[::-1].hex(),
        merkle_root=merkle_root[::-1].hex(),
        header_hex=header.hex(),
    )
