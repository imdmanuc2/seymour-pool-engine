#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Callable


DIFF1_TARGET = 0x00FFFF << (8 * (0x1D - 3))


def sha256d(value: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(value).digest()).digest()


def reverse_words_4(value: bytes) -> bytes:
    if len(value) % 4:
        raise ValueError("value length must be divisible by four")

    return b"".join(
        value[index:index + 4][::-1]
        for index in range(0, len(value), 4)
    )


def reverse_word_order(value: bytes) -> bytes:
    if len(value) % 4:
        raise ValueError("value length must be divisible by four")

    words = [
        value[index:index + 4]
        for index in range(0, len(value), 4)
    ]

    return b"".join(reversed(words))


def difficulty(hash_value: int) -> Decimal:
    with localcontext() as context:
        context.prec = 100
        return Decimal(DIFF1_TARGET) / Decimal(max(hash_value, 1))


def load_json(path: str) -> dict:
    content = Path(path).read_text(encoding="utf-8").strip()

    if not content:
        raise RuntimeError(f"{path} is empty")

    return json.loads(content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test Bitcoin Stratum header byte-order permutations."
    )
    parser.add_argument(
        "--job-json",
        default="/tmp/seymour-job-5720cce6.json",
    )
    parser.add_argument(
        "--share-json",
        default="/tmp/seymour-share-5720cce6.json",
    )
    parser.add_argument(
        "--extranonce1",
        required=True,
    )
    parser.add_argument(
        "--version-bits",
        required=True,
    )
    parser.add_argument(
        "--version-mask",
        default="1fffe000",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
    )
    args = parser.parse_args()

    job = load_json(args.job_json)
    share = load_json(args.share_json)

    coinbase_hex = (
        job["coinbase1"]
        + args.extranonce1
        + share["extranonce2"]
        + job["coinbase2"]
    )

    coinbase = bytes.fromhex(coinbase_hex)
    coinbase_hash = sha256d(coinbase)

    base_version = int(job["version"], 16)
    submitted_bits = int(args.version_bits, 16)
    mask = int(args.version_mask, 16)

    effective_version = (
        (base_version & ~mask)
        | (submitted_bits & mask)
    )

    prevhash = bytes.fromhex(job["previous_block_hash"])
    ntime = bytes.fromhex(share["ntime"])
    bits = bytes.fromhex(job["nbits"])
    nonce = bytes.fromhex(share["nonce"])

    transforms: dict[str, Callable[[bytes], bytes]] = {
        "raw": lambda value: value,
        "full-reverse": lambda value: value[::-1],
        "reverse-each-32bit-word": reverse_words_4,
        "reverse-32bit-word-order": reverse_word_order,
        "word-swap-plus-full-reverse": (
            lambda value: reverse_words_4(value)[::-1]
        ),
    }

    branch_modes = {
        "branch-raw": lambda value: value,
        "branch-reversed": lambda value: value[::-1],
    }

    results: list[dict] = []

    for branch_mode_name, branch_transform in branch_modes.items():
        merkle_internal = coinbase_hash

        for branch_hex in job["merkle_branches"]:
            branch = branch_transform(bytes.fromhex(branch_hex))
            merkle_internal = sha256d(merkle_internal + branch)

        merkle_options = {
            "merkle-internal": merkle_internal,
            "merkle-reversed": merkle_internal[::-1],
            "merkle-word-swapped": reverse_words_4(merkle_internal),
        }

        for prev_name, prev_transform in transforms.items():
            previous = prev_transform(prevhash)

            for merkle_name, merkle in merkle_options.items():
                for ntime_name, ntime_bytes in {
                    "ntime-reversed": ntime[::-1],
                    "ntime-raw": ntime,
                }.items():
                    for nonce_name, nonce_bytes in {
                        "nonce-reversed": nonce[::-1],
                        "nonce-raw": nonce,
                    }.items():
                        for version_name, version_bytes in {
                            "version-little": effective_version.to_bytes(
                                4,
                                "little",
                            ),
                            "version-big": effective_version.to_bytes(
                                4,
                                "big",
                            ),
                        }.items():
                            for bits_name, bits_bytes in {
                                "bits-reversed": bits[::-1],
                                "bits-raw": bits,
                            }.items():
                                header = (
                                    version_bytes
                                    + previous
                                    + merkle
                                    + ntime_bytes
                                    + bits_bytes
                                    + nonce_bytes
                                )

                                digest = sha256d(header)

                                hash_value = int.from_bytes(
                                    digest,
                                    "little",
                                )

                                achieved = difficulty(hash_value)

                                results.append(
                                    {
                                        "difficulty": achieved,
                                        "hash": digest[::-1].hex(),
                                        "header": header.hex(),
                                        "mode": " | ".join(
                                            [
                                                branch_mode_name,
                                                prev_name,
                                                merkle_name,
                                                ntime_name,
                                                bits_name,
                                                nonce_name,
                                                version_name,
                                            ]
                                        ),
                                    }
                                )

    results.sort(
        key=lambda item: item["difficulty"],
        reverse=True,
    )

    print("Stored Seymour result")
    print("---------------------")
    print(f"share hash:       {share.get('share_hash')}")
    print(f"share difficulty: {share.get('share_difficulty')}")
    print(f"stored header:    {share.get('header_hex')}")
    print()

    print("Inputs")
    print("------")
    print(f"job:               {job['job_id']}")
    print(f"extranonce1:       {args.extranonce1}")
    print(f"extranonce2:       {share['extranonce2']}")
    print(f"ntime:             {share['ntime']}")
    print(f"nonce:             {share['nonce']}")
    print(f"version bits:      {args.version_bits}")
    print(f"effective version: {effective_version:08x}")
    print(f"coinbase hash:     {coinbase_hash[::-1].hex()}")
    print()

    print(f"Top {args.limit} reconstructed difficulties")
    print("-------------------------------------------")

    for index, result in enumerate(results[:args.limit], start=1):
        print()
        print(f"{index:02d}. difficulty: {result['difficulty']}")
        print(f"    mode:   {result['mode']}")
        print(f"    hash:   {result['hash']}")
        print(f"    header: {result['header']}")


if __name__ == "__main__":
    main()
