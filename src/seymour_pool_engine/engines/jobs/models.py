from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class BitcoinTransaction:
    txid: str
    hash: str
    data: str
    fee: int = 0
    sigops: int = 0
    weight: int = 0


@dataclass(frozen=True, slots=True)
class BitcoinBlockTemplate:
    height: int
    previous_block_hash: str
    version: int
    bits: str
    curtime: int
    mintime: int
    coinbase_value: int
    transactions: tuple[BitcoinTransaction, ...]

    target: str | None = None
    work_id: str | None = None
    longpoll_id: str | None = None

    rules: tuple[str, ...] = ()
    vbavailable: dict[str, int] = field(default_factory=dict)
    vbrequired: int = 0
    mutable: tuple[str, ...] = ()
    noncerange: str | None = None
    coinbaseaux: dict[str, str] = field(default_factory=dict)
    default_witness_commitment: str | None = None
    coinbasetxn: dict[str, Any] | None = None

    @classmethod
    def from_rpc(cls, payload: dict[str, Any]) -> BitcoinBlockTemplate:
        required = (
            "height",
            "previousblockhash",
            "version",
            "bits",
            "curtime",
            "coinbasevalue",
        )
        missing = [name for name in required if name not in payload]

        if missing:
            raise ValueError(
                f"getblocktemplate missing fields: {', '.join(missing)}"
            )

        transactions = tuple(
            BitcoinTransaction(
                txid=str(transaction["txid"]),
                hash=str(
                    transaction.get(
                        "hash",
                        transaction["txid"],
                    )
                ),
                data=str(transaction["data"]),
                fee=int(transaction.get("fee", 0)),
                sigops=int(transaction.get("sigops", 0)),
                weight=int(transaction.get("weight", 0)),
            )
            for transaction in payload.get("transactions", [])
        )

        raw_vbavailable = payload.get("vbavailable") or {}
        raw_coinbaseaux = payload.get("coinbaseaux") or {}
        raw_coinbasetxn = payload.get("coinbasetxn")

        return cls(
            height=int(payload["height"]),
            previous_block_hash=str(payload["previousblockhash"]),
            version=int(payload["version"]),
            bits=str(payload["bits"]),
            curtime=int(payload["curtime"]),
            mintime=int(payload.get("mintime", payload["curtime"])),
            coinbase_value=int(payload["coinbasevalue"]),
            transactions=transactions,
            target=(
                str(payload["target"])
                if payload.get("target") is not None
                else None
            ),
            work_id=(
                str(payload["workid"])
                if payload.get("workid") is not None
                else None
            ),
            longpoll_id=(
                str(payload["longpollid"])
                if payload.get("longpollid") is not None
                else None
            ),
            rules=tuple(
                str(rule)
                for rule in payload.get("rules", [])
            ),
            vbavailable={
                str(name): int(bit)
                for name, bit in raw_vbavailable.items()
            },
            vbrequired=int(payload.get("vbrequired", 0)),
            mutable=tuple(
                str(value)
                for value in payload.get("mutable", [])
            ),
            noncerange=(
                str(payload["noncerange"])
                if payload.get("noncerange") is not None
                else None
            ),
            coinbaseaux={
                str(name): str(value)
                for name, value in raw_coinbaseaux.items()
            },
            default_witness_commitment=(
                str(payload["default_witness_commitment"])
                if payload.get("default_witness_commitment") is not None
                else None
            ),
            coinbasetxn=(
                dict(raw_coinbasetxn)
                if isinstance(raw_coinbasetxn, dict)
                else None
            ),
        )


@dataclass(frozen=True, slots=True)
class StratumJob:
    job_id: str
    template_height: int
    previous_block_hash: str
    coinbase1: str
    coinbase2: str
    merkle_branches: tuple[str, ...]
    version: str
    nbits: str
    ntime: str
    clean_jobs: bool
    source: str = "bitcoin-rpc"
    coinbase_value: int = 0
    transaction_count: int = 0
    work_id: str | None = None

    def notify_params(self) -> list[object]:
        return [
            self.job_id,
            self.previous_block_hash,
            self.coinbase1,
            self.coinbase2,
            list(self.merkle_branches),
            self.version,
            self.nbits,
            self.ntime,
            self.clean_jobs,
        ]