from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from seymour_pool_engine.services.block_service import BlockService


class FakeRepository:
    def __init__(self) -> None:
        self.observations = []

    def upsert(self, **kwargs):
        self.observations = kwargs["observations"]
        return {"inserted": len(self.observations), "updated": 0, "events": len(self.observations)}

    def list_blocks(self, **kwargs):
        now = datetime.now(UTC)
        return [
            {
                "block_id": uuid4(),
                "provider_name": "synthetic",
                "provider_block_key": "block-1",
                "pool_id": "btc-solo",
                "block_height": 900001,
                "block_hash": "00abc",
                "status": "confirmed",
                "confirmations": 120,
                "network_difficulty": 100.0,
                "reward": Decimal("3.125"),
                "miner": "seymour",
                "worker": "001",
                "share_id": None,
                "found_at": now,
                "confirmed_at": now,
                "orphaned_at": None,
                "last_checked_at": now,
                "created_at": now,
                "updated_at": now,
                "metadata": {},
            }
        ]

    def statistics(self, **kwargs):
        return {
            "total_blocks": 4,
            "candidate_blocks": 1,
            "immature_blocks": 1,
            "confirmed_blocks": 1,
            "orphaned_blocks": 1,
            "confirmed_reward": Decimal("3.125"),
            "last_block_at": datetime.now(UTC),
        }


def test_sync_normalizes_and_persists_observations() -> None:
    repository = FakeRepository()
    service = BlockService(repository)
    result = service.synchronize(
        provider_name="synthetic",
        observations=[
            {
                "provider_block_key": "block-1",
                "pool_id": "btc-solo",
                "block_height": 900001,
                "status": "confirmed",
                "confirmations": 120,
                "found_at": datetime.now(UTC),
            }
        ],
    )
    assert result["inserted"] == 1
    assert repository.observations[0]["confirmed_at"] is not None


def test_list_and_statistics_contracts() -> None:
    service = BlockService(FakeRepository())
    assert service.list_blocks()["blocks"][0]["reward"] == 3.125
    assert service.statistics()["orphanedBlocks"] == 1


def test_invalid_status_limit_and_confirmations_are_rejected() -> None:
    service = BlockService(FakeRepository())
    calls = (
        lambda: service.list_blocks(status="paid"),
        lambda: service.list_blocks(limit=5001),
        lambda: service.synchronize(
            provider_name="synthetic",
            observations=[
                {
                    "provider_block_key": "bad",
                    "pool_id": "btc-solo",
                    "block_height": 1,
                    "status": "candidate",
                    "confirmations": -1,
                    "found_at": datetime.now(UTC),
                }
            ],
        ),
    )
    for call in calls:
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("Expected ValueError")
