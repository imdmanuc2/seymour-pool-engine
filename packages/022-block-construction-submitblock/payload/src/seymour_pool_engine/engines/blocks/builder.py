from __future__ import annotations

from dataclasses import dataclass

from seymour_pool_engine.engines.jobs.models import BitcoinBlockTemplate, StratumJob
from seymour_pool_engine.engines.shares.validator import ShareValidationResult


class BlockAssemblyError(ValueError):
    """Raised when a validated candidate cannot be serialized as a block."""


@dataclass(frozen=True, slots=True)
class AssembledBlock:
    block_hash: str
    header_hex: str
    block_hex: str
    coinbase_hex: str
    transaction_count: int


def encode_varint(value: int) -> bytes:
    if value < 0:
        raise BlockAssemblyError("compact size cannot be negative")
    if value < 0xFD:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + value.to_bytes(2, "little")
    if value <= 0xFFFFFFFF:
        return b"\xfe" + value.to_bytes(4, "little")
    if value <= 0xFFFFFFFFFFFFFFFF:
        return b"\xff" + value.to_bytes(8, "little")
    raise BlockAssemblyError("compact size exceeds uint64")


def _decode_hex(value: str, name: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise BlockAssemblyError(f"{name} is not valid hexadecimal") from exc


def assemble_block(
    *,
    job: StratumJob,
    template: BitcoinBlockTemplate,
    validation: ShareValidationResult,
    extranonce1: str,
    extranonce2: str,
) -> AssembledBlock:
    if not validation.block_candidate:
        raise BlockAssemblyError("share does not meet the network target")
    if template.height != job.template_height:
        raise BlockAssemblyError("job and template heights do not match")
    if template.previous_block_hash != job.previous_block_hash:
        raise BlockAssemblyError("job and template previous hashes do not match")

    coinbase_hex = job.coinbase1 + extranonce1 + extranonce2 + job.coinbase2
    coinbase = _decode_hex(coinbase_hex, "coinbase transaction")
    header = _decode_hex(validation.header_hex, "block header")
    if len(header) != 80:
        raise BlockAssemblyError("block header must be exactly 80 bytes")

    transactions = [_decode_hex(tx.data, f"transaction {tx.txid}") for tx in template.transactions]
    count = 1 + len(transactions)
    block = header + encode_varint(count) + coinbase + b"".join(transactions)
    return AssembledBlock(
        block_hash=validation.hash_hex,
        header_hex=validation.header_hex,
        block_hex=block.hex(),
        coinbase_hex=coinbase_hex,
        transaction_count=count,
    )
