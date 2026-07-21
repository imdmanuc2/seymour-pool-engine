import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SyntheticJob:
    job_id: str
    previous_block_hash: str
    coinbase1: str
    coinbase2: str
    merkle_branches: list[str]
    version: str
    nbits: str
    ntime: str
    clean_jobs: bool

    def notify_params(self) -> list[object]:
        return [
            self.job_id,
            self.previous_block_hash,
            self.coinbase1,
            self.coinbase2,
            self.merkle_branches,
            self.version,
            self.nbits,
            self.ntime,
            self.clean_jobs,
        ]


def create_synthetic_job() -> SyntheticJob:
    return SyntheticJob(
        secrets.token_hex(8),
        "00" * 32,
        "0100000001" + ("00" * 32) + "ffffffff",
        "ffffffff0100000000000000000000000000",
        [],
        "20000000",
        "1d00ffff",
        f"{int(time.time()):08x}",
        True,
    )
