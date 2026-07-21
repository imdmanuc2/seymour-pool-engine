from __future__ import annotations

import hashlib
import secrets
from collections.abc import Iterable

from seymour_pool_engine.engines.jobs.models import BitcoinBlockTemplate, StratumJob


def _double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint cannot be negative")
    if value < 0xFD:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + value.to_bytes(2, "little")
    if value <= 0xFFFFFFFF:
        return b"\xfe" + value.to_bytes(4, "little")
    return b"\xff" + value.to_bytes(8, "little")


def _script_number(value: int) -> bytes:
    if value == 0:
        return b""
    result = bytearray()
    negative = value < 0
    absolute = -value if negative else value
    while absolute:
        result.append(absolute & 0xFF)
        absolute >>= 8
    if result[-1] & 0x80:
        result.append(0x80 if negative else 0)
    elif negative:
        result[-1] |= 0x80
    return bytes(result)


def _push(data: bytes) -> bytes:
    if len(data) > 75:
        raise ValueError("coinbase push exceeds compact push limit")
    return bytes([len(data)]) + data


def build_merkle_branches(transaction_hashes: Iterable[str]) -> tuple[str, ...]:
    """Build coinbase merkle branches from Bitcoin Core internal-order hashes."""
    level = [bytes.fromhex(value)[::-1] for value in transaction_hashes]
    branches: list[str] = []
    index = 0
    while level:
        if len(level) % 2:
            level.append(level[-1])
        sibling = level[index ^ 1] if len(level) > 1 else level[0]
        branches.append(sibling[::-1].hex())
        next_level = [_double_sha256(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
        index //= 2
        level = next_level
        if len(level) == 1:
            break
    return tuple(branches)


def build_coinbase_parts(
    template: BitcoinBlockTemplate,
    payout_script_hex: str,
    extranonce1_size: int = 6,
    extranonce2_size: int = 4,
    coinbase_tag: str = "/Seymour/",
) -> tuple[str, str]:
    payout_script = bytes.fromhex(payout_script_hex)
    height = _script_number(template.height)
    script_prefix = _push(height) + coinbase_tag.encode("utf-8")
    placeholder_size = extranonce1_size + extranonce2_size
    script_length = len(script_prefix) + placeholder_size
    if script_length > 100:
        raise ValueError("coinbase scriptSig exceeds 100 bytes")

    prefix = (
        (2).to_bytes(4, "little")
        + b"\x01"
        + (b"\x00" * 32)
        + (0xFFFFFFFF).to_bytes(4, "little")
        + _encode_varint(script_length)
        + script_prefix
    )
    suffix = (
        (0xFFFFFFFF).to_bytes(4, "little")
        + b"\x01"
        + template.coinbase_value.to_bytes(8, "little")
        + _encode_varint(len(payout_script))
        + payout_script
        + (0).to_bytes(4, "little")
    )
    return prefix.hex(), suffix.hex()


def create_stratum_job(
    template: BitcoinBlockTemplate,
    payout_script_hex: str,
    extranonce1_size: int = 6,
    extranonce2_size: int = 4,
    clean_jobs: bool = True,
    coinbase_tag: str = "/Seymour/",
) -> StratumJob:
    coinbase1, coinbase2 = build_coinbase_parts(
        template,
        payout_script_hex,
        extranonce1_size,
        extranonce2_size,
        coinbase_tag,
    )
    tx_hashes = (tx.hash for tx in template.transactions)
    return StratumJob(
        job_id=secrets.token_hex(8),
        template_height=template.height,
        previous_block_hash=template.previous_block_hash,
        coinbase1=coinbase1,
        coinbase2=coinbase2,
        merkle_branches=build_merkle_branches(tx_hashes),
        version=f"{template.version:08x}",
        nbits=template.bits,
        ntime=f"{template.curtime:08x}",
        clean_jobs=clean_jobs,
        coinbase_value=template.coinbase_value,
        transaction_count=len(template.transactions),
        work_id=template.work_id,
    )
