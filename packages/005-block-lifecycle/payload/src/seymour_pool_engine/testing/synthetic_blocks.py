from datetime import UTC, datetime, timedelta
from random import Random
from typing import Any


def generate_synthetic_blocks(
    *,
    pool_id: str = "btc-solo",
    count: int = 6,
    seed: int = 5005,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    if count < 1:
        raise ValueError("Synthetic block count must be positive")
    rng = Random(seed)
    observed_at = end or datetime.now(UTC)
    states = ("candidate", "immature", "confirmed", "orphaned")
    blocks: list[dict[str, Any]] = []
    for index in range(count):
        status = states[index % len(states)]
        confirmations = 0
        if status == "immature":
            confirmations = rng.randint(1, 99)
        elif status == "confirmed":
            confirmations = rng.randint(100, 300)
        found_at = observed_at - timedelta(minutes=index * 11)
        blocks.append(
            {
                "provider_block_key": f"synthetic-{seed}-{index}",
                "pool_id": pool_id,
                "block_height": 900_000 + index,
                "block_hash": f"{seed:08x}{index:056x}",
                "status": status,
                "confirmations": confirmations,
                "network_difficulty": 120_000_000_000_000.0,
                "reward": 3.125,
                "miner": "seymour",
                "worker": f"{index + 1:03d}",
                "found_at": found_at,
                "confirmed_at": observed_at if status == "confirmed" else None,
                "orphaned_at": observed_at if status == "orphaned" else None,
                "last_checked_at": observed_at,
                "metadata": {"synthetic": True, "seed": seed},
            }
        )
    return blocks
