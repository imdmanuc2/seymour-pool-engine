from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections.abc import Iterable
from pathlib import Path

from seymour_pool_engine.engines.jobs.models import BitcoinBlockTemplate, StratumJob


def _double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _stratum_prevhash(previous_block_hash: str) -> str:
    """Convert a Bitcoin Core block hash to Stratum prevhash word order.

    CKPool's swap_256 operation reverses the order of the eight 32-bit
    words while preserving the byte order inside each word.
    """
    raw = bytes.fromhex(previous_block_hash)

    if len(raw) != 32:
        raise ValueError("previous block hash must be exactly 32 bytes")

    words = [raw[index:index + 4] for index in range(0, 32, 4)]
    return b"".join(reversed(words)).hex()


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
    """Build the merkle path for a variable coinbase at tree index zero.

    Bitcoin Core getblocktemplate transaction hashes are conventional txid
    strings. They are converted to internal byte order before merkle hashing.

    The coinbase hash is represented by None because it is not known until a
    miner supplies extranonce values. At each level, the sibling beside that
    unknown node is added to the Stratum merkle branch.
    """
    transaction_nodes = [
        bytes.fromhex(value)[::-1]
        for value in transaction_hashes
    ]

    if not transaction_nodes:
        return ()

    level: list[bytes | None] = [None, *transaction_nodes]
    branches: list[str] = []

    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])

        sibling = level[1]
        if sibling is None:
            raise ValueError("coinbase merkle sibling cannot be unknown")

        # Stratum merkle branches are serialized in internal hashing byte order.
        branches.append(sibling.hex())

        next_level: list[bytes | None] = []

        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1]

            if left is None or right is None:
                next_level.append(None)
            else:
                next_level.append(_double_sha256(left + right))

        level = next_level

    return tuple(branches)


def _serialize_script_number(value: int) -> bytes:
    """Python equivalent of CKPool ser_number().

    Serialize an integer as a minimally encoded Bitcoin Script number and
    prefix it with its byte length.
    """
    encoded = _script_number(value)

    if len(encoded) > 75:
        raise ValueError("serialized script number exceeds direct push limit")

    return bytes([len(encoded)]) + encoded


def _coinbase_aux_flags(template: BitcoinBlockTemplate) -> bytes:
    """Return Bitcoin Core coinbaseaux.flags as raw bytes.

    This supports the most likely Seymour model representations while allowing
    older templates that do not yet expose coinbase flags.
    """
    flags_hex = getattr(template, "coinbase_aux_flags", None)

    if flags_hex is None:
        coinbase_aux = getattr(template, "coinbase_aux", None)

        if isinstance(coinbase_aux, dict):
            flags_hex = coinbase_aux.get("flags")
        elif coinbase_aux is not None:
            flags_hex = getattr(coinbase_aux, "flags", None)

    if not flags_hex:
        return b""

    if not isinstance(flags_hex, str):
        raise ValueError("coinbaseaux.flags must be a hexadecimal string")

    try:
        return bytes.fromhex(flags_hex)
    except ValueError as exc:
        raise ValueError(
            "coinbaseaux.flags contains invalid hexadecimal data"
        ) from exc


def build_coinbase_parts(
    template: BitcoinBlockTemplate,
    payout_script_hex: str,
    extranonce1_size: int = 4,
    extranonce2_size: int = 8,
    coinbase_tag: str = "/Seymour/",
) -> tuple[str, str]:
    """Build a CKPool-style Bitcoin coinbase split.

    Wire layout:

        coinbase1:
            transaction version
            one coinbase input
            null previous output
            scriptSig length
            serialized block height
            pushed coinbaseaux.flags
            serialized current timestamp
            serialized nanosecond randomizer
            extranonce push length

        miner inserts:
            extranonce1
            extranonce2

        coinbase2:
            pushed Seymour signature
            sequence
            outputs
            locktime
    """
    try:
        payout_script = bytes.fromhex(payout_script_hex)
    except ValueError as exc:
        raise ValueError("payout script contains invalid hexadecimal data") from exc

    extranonce_size = extranonce1_size + extranonce2_size

    if extranonce1_size <= 0:
        raise ValueError("extranonce1 size must be positive")

    if extranonce2_size <= 0:
        raise ValueError("extranonce2 size must be positive")

    if extranonce_size > 75:
        raise ValueError(
            "combined extranonce size exceeds direct script push limit"
        )

    tag_bytes = coinbase_tag.encode("utf-8")

    if len(tag_bytes) > 75:
        raise ValueError("coinbase tag exceeds direct script push limit")

    # CKPool uses the current real-time clock rather than GBT curtime for these
    # two scriptSig uniqueness fields.
    now_ns = time.time_ns()
    timestamp_seconds = now_ns // 1_000_000_000
    nanosecond_randomizer = now_ns % 1_000_000_000

    height_part = _serialize_script_number(template.height)

    flags = _coinbase_aux_flags(template)

    # CKPool writes:
    #
    #     coinb1bin[ofs++] = len;
    #     hex2bin(... flags ...)
    #
    # Therefore the flags have a one-byte push length.
    if len(flags) > 75:
        raise ValueError("coinbaseaux.flags exceeds direct push limit")

    flags_part = bytes([len(flags)]) + flags

    timestamp_part = _serialize_script_number(timestamp_seconds)
    randomizer_part = _serialize_script_number(nanosecond_randomizer)

    # CKPool leaves the actual extranonce bytes out of coinbase1. The miner
    # inserts extranonce1 and extranonce2 between coinbase1 and coinbase2.
    extranonce_push = bytes([extranonce_size])

    tag_part = bytes([len(tag_bytes)]) + tag_bytes

    script_sig_length = (
        len(height_part)
        + len(flags_part)
        + len(timestamp_part)
        + len(randomizer_part)
        + len(extranonce_push)
        + extranonce_size
        + len(tag_part)
    )

    if script_sig_length > 100:
        raise ValueError(
            f"coinbase scriptSig is {script_sig_length} bytes; maximum is 100"
        )

    coinbase1 = (
        # Transaction version 1.
        (1).to_bytes(4, "little")

        # One transaction input.
        + _encode_varint(1)

        # Null previous transaction hash.
        + (b"\x00" * 32)

        # Coinbase previous-output index.
        + (0xFFFFFFFF).to_bytes(4, "little")

        # Full scriptSig size, including miner-provided extranonces.
        + _encode_varint(script_sig_length)

        # CKPool-compatible scriptSig prefix.
        + height_part
        + flags_part
        + timestamp_part
        + randomizer_part
        + extranonce_push
    )

    outputs: list[bytes] = [
        (
            template.coinbase_value.to_bytes(8, "little")
            + _encode_varint(len(payout_script))
            + payout_script
        )
    ]

    if template.default_witness_commitment:
        try:
            witness_commitment = bytes.fromhex(
                template.default_witness_commitment
            )
        except ValueError as exc:
            raise ValueError(
                "default witness commitment contains invalid hexadecimal data"
            ) from exc

        if not witness_commitment.startswith(
            bytes.fromhex("6a24aa21a9ed")
        ):
            raise ValueError(
                "default witness commitment has an unexpected script"
            )

        outputs.append(
            (0).to_bytes(8, "little")
            + _encode_varint(len(witness_commitment))
            + witness_commitment
        )

    coinbase2 = (
        # Remaining scriptSig bytes after the miner's extranonces.
        tag_part

        # Coinbase input sequence.
        + (0xFFFFFFFF).to_bytes(4, "little")

        # Transaction outputs.
        + _encode_varint(len(outputs))
        + b"".join(outputs)

        # Locktime.
        + (0).to_bytes(4, "little")
    )

    return coinbase1.hex(), coinbase2.hex()


def create_stratum_job(
    template: BitcoinBlockTemplate,
    payout_script_hex: str,
    extranonce1_size: int = 4,
    extranonce2_size: int = 8,
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
    job_id = secrets.token_hex(8)
    tx_hashes = tuple(tx.txid for tx in template.transactions)
    merkle_branches = build_merkle_branches(tx_hashes)

    job = StratumJob(
        job_id=job_id,
        template_height=template.height,
        previous_block_hash=_stratum_prevhash(
            template.previous_block_hash
        ),
        coinbase1=coinbase1,
        coinbase2=coinbase2,
        merkle_branches=merkle_branches,
        version=f"{template.version:08x}",
        nbits=template.bits,
        ntime=f"{template.curtime:08x}",
        clean_jobs=clean_jobs,
        coinbase_value=template.coinbase_value,
        transaction_count=len(template.transactions),
        work_id=template.work_id,
    )

    diagnostic_payload = {
        "job_id": job_id,
        "height": template.height,
        "previousblockhash": template.previous_block_hash,
        "stratum_prevhash": job.previous_block_hash,
        "version": template.version,
        "bits": template.bits,
        "curtime": template.curtime,
        "coinbasevalue": template.coinbase_value,
        "coinbase1": coinbase1,
        "coinbase2": coinbase2,
        "transactions": [
            {
                "txid": transaction.txid,
                "hash": transaction.hash,
            }
            for transaction in template.transactions
        ],
        "merkle_branches": list(merkle_branches),
    }

    diagnostic_path = Path(
        f"/tmp/seymour-job-{job_id}-template.json"
    )

    diagnostic_path.write_text(
        json.dumps(
            diagnostic_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return job
