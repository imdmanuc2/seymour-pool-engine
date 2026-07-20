from datetime import UTC, datetime, timedelta
from random import Random

from seymour_pool_engine.providers.models import ShareSummary


def generate_synthetic_shares(
    *,
    pool_id: str = "btc-solo",
    workers: int = 10,
    shares_per_worker: int = 25,
    seed: int = 1,
    end_at: datetime | None = None,
) -> list[ShareSummary]:
    """Create deterministic share observations for tests and controlled load exercises."""
    if workers < 1 or shares_per_worker < 1:
        raise ValueError("workers and shares_per_worker must be positive")
    rng = Random(seed)
    end = end_at or datetime.now(UTC)
    shares: list[ShareSummary] = []
    for worker_number in range(1, workers + 1):
        worker = f"{worker_number:04d}"
        for share_number in range(shares_per_worker):
            status_roll = rng.random()
            status = "accepted" if status_roll < 0.94 else "stale" if status_roll < 0.98 else "rejected"
            created_at = end - timedelta(seconds=rng.randint(0, 3599))
            shares.append(
                ShareSummary(
                    providerShareKey=(
                        f"synthetic:{seed}:{pool_id}:{worker}:{share_number}"
                    ),
                    poolId=pool_id,
                    miner="synthetic",
                    worker=worker,
                    difficulty=float(2 ** rng.randint(8, 16)),
                    createdAt=created_at,
                    metadata={"shareStatus": status, "synthetic": True},
                )
            )
    return shares
