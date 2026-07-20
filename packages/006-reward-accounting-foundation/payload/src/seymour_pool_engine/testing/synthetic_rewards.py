from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID


def synthetic_reward_request(block_id: UUID) -> dict:
    end_at = datetime.now(UTC)
    return {
        "block_id": block_id,
        "pool_id": "btc-solo",
        "gross_reward": Decimal("3.125"),
        "fee_percent": Decimal("0.75"),
        "start_at": end_at - timedelta(hours=1),
        "end_at": end_at,
    }
