from datetime import UTC, datetime
from uuid import uuid4

from seymour_pool_engine.providers.models import ShareSummary
from seymour_pool_engine.services.share_service import ShareService


class FakeProvider:
    def list_shares(self, **kwargs) -> list[ShareSummary]:
        return [
            ShareSummary(
                providerShareKey="share-key-1",
                poolId=kwargs.get("pool_id") or "btc-solo",
                miner="seymour",
                worker="001",
                difficulty=1024,
                networkDifficulty=2048,
                blockHeight=900000,
                ipAddress="127.0.0.1",
                userAgent="test-miner",
                createdAt=datetime.now(UTC),
            )
        ]


class FakeRepository:
    def __init__(self) -> None:
        self.ingest_args = None

    def ingest(self, **kwargs):
        self.ingest_args = kwargs
        return {"observed": 1, "inserted": 1, "duplicates": 0}

    def list_shares(self, **kwargs):
        now = datetime.now(UTC)
        return [
            {
                "share_id": uuid4(),
                "provider_name": "miningcore",
                "provider_share_key": "share-key-1",
                "worker_id": uuid4(),
                "pool_id": "btc-solo",
                "miner": "seymour",
                "worker": "001",
                "difficulty": 1024.0,
                "network_difficulty": 2048.0,
                "block_height": 900000,
                "ip_address": "127.0.0.1",
                "user_agent": "test-miner",
                "provider_created_at": now,
                "ingested_at": now,
                "metadata": {},
            }
        ]


def test_share_sync_ingests_provider_observations() -> None:
    repository = FakeRepository()
    service = ShareService(repository=repository, provider=FakeProvider())

    result = service.synchronize(pool_id="btc-solo", limit=250)

    assert result["provider"] == "miningcore"
    assert result["inserted"] == 1
    assert repository.ingest_args["provider_name"] == "miningcore"
    assert len(repository.ingest_args["observations"]) == 1


def test_share_list_returns_spe_contract() -> None:
    service = ShareService(repository=FakeRepository(), provider=FakeProvider())

    result = service.list_shares(pool_id="btc-solo", limit=10)

    assert result["count"] == 1
    assert result["shares"][0]["shareId"]
    assert result["shares"][0]["provider"] == "miningcore"
    assert result["shares"][0]["poolId"] == "btc-solo"


def test_share_limit_validation() -> None:
    service = ShareService(repository=FakeRepository(), provider=FakeProvider())

    try:
        service.list_shares(limit=5001)
    except ValueError as exc:
        assert "Share limit must be between" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
