from datetime import UTC, datetime
from uuid import uuid4

import pytest

from seymour_pool_engine.services.statistics_service import HASHES_PER_DIFFICULTY, StatisticsService


class FakeRepository:
    def overview(self, *, since):
        return {
            "accepted_difficulty": 300.0,
            "accepted_shares": 3,
            "rejected_shares": 1,
            "active_workers": 2,
            "last_share_at": datetime.now(UTC),
            "last_accepted_at": datetime.now(UTC),
        }

    def workers(self, *, since, limit):
        return [self._worker()]

    def worker(self, *, worker_name, since):
        return self._worker() if worker_name == "wallet.001" else None

    def engine(self, *, since):
        return {
            "active_sessions": 2,
            "connected_workers": 2,
            "authorized_sessions": 2,
            "submissions": 120,
            "accepted": 100,
            "rejected": 20,
            "latest_submission": datetime.now(UTC),
            "messages_received": 500,
            "messages_sent": 500,
        }

    @staticmethod
    def _worker():
        now = datetime.now(UTC)
        return {
            "worker_name": "wallet.001",
            "accepted_difficulty": 300.0,
            "accepted_shares": 3,
            "rejected_shares": 1,
            "last_share_at": now,
            "last_accepted_at": now,
            "session_id": uuid4(),
            "remote_host": "192.168.1.151",
            "remote_port": 12345,
            "connected_at": now,
            "disconnected_at": None,
            "authorized": True,
            "difficulty": 100.0,
            "last_activity_at": now,
        }


def test_overview_hashrate_uses_assigned_share_work() -> None:
    result = StatisticsService(FakeRepository()).overview(window="5m")
    assert result["hashrate"] == pytest.approx(300 * HASHES_PER_DIFFICULTY / 300)
    assert result["activeWorkers"] == 2
    assert result["efficiency"] == pytest.approx(0.75)
    assert result["source"] == "seymour-native-stratum"


def test_worker_status_and_hashrate() -> None:
    result = StatisticsService(FakeRepository()).worker("wallet.001", window="5m")
    assert result is not None
    assert result["phase"] == "stable"
    assert result["online"] is True
    assert result["hashrate"] > 0


def test_engine_metrics() -> None:
    result = StatisticsService(FakeRepository()).engine(window="1m")
    assert result["connectedWorkers"] == 2
    assert result["submissionsPerSecond"] == pytest.approx(2.0)
    assert result["queueTelemetryAvailable"] is False


def test_invalid_window() -> None:
    with pytest.raises(ValueError, match="Unsupported statistics window"):
        StatisticsService(FakeRepository()).overview(window="2m")
