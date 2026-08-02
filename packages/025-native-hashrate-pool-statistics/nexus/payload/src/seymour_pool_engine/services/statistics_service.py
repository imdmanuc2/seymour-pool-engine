from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from seymour_pool_engine.repositories.statistics_repository import StatisticsRepository

HASHES_PER_DIFFICULTY = 2**32
WINDOWS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}
MAX_WORKERS_LIMIT = 5000


class StatisticsService:
    def __init__(self, repository: StatisticsRepository | None = None) -> None:
        self.repository = repository or StatisticsRepository()

    @staticmethod
    def _window(window: str) -> tuple[int, datetime]:
        try:
            seconds = WINDOWS[window]
        except KeyError as exc:
            raise ValueError(f"Unsupported statistics window: {window}") from exc
        return seconds, datetime.now(UTC) - timedelta(seconds=seconds)

    @staticmethod
    def _hashrate(accepted_difficulty: float, seconds: int) -> float:
        return float(accepted_difficulty or 0) * HASHES_PER_DIFFICULTY / seconds

    @staticmethod
    def _rates(accepted: int, rejected: int) -> dict[str, float | int]:
        total = accepted + rejected
        return {
            "totalShares": total,
            "efficiency": accepted / total if total else 0.0,
            "rejectionRate": rejected / total if total else 0.0,
        }

    @staticmethod
    def _iso(value: Any) -> str | None:
        return value.isoformat() if value else None

    def overview(self, *, window: str = "5m") -> dict[str, Any]:
        seconds, since = self._window(window)
        row = self.repository.overview(since=since)
        accepted = int(row.get("accepted_shares") or 0)
        rejected = int(row.get("rejected_shares") or 0)
        return {
            "source": "seymour-native-stratum",
            "scope": {"type": "pool", "id": "btc-solo"},
            "window": window,
            "windowSeconds": seconds,
            "calculatedAt": datetime.now(UTC).isoformat(),
            "hashrate": self._hashrate(float(row.get("accepted_difficulty") or 0), seconds),
            "activeWorkers": int(row.get("active_workers") or 0),
            "acceptedShares": accepted,
            "rejectedShares": rejected,
            "lastShareAt": self._iso(row.get("last_share_at")),
            "lastAcceptedAt": self._iso(row.get("last_accepted_at")),
            **self._rates(accepted, rejected),
        }

    def workers(self, *, window: str = "5m", limit: int = 100) -> dict[str, Any]:
        if limit < 1 or limit > MAX_WORKERS_LIMIT:
            raise ValueError(f"Worker statistics limit must be between 1 and {MAX_WORKERS_LIMIT}")
        seconds, since = self._window(window)
        rows = self.repository.workers(since=since, limit=limit)
        workers = [self._serialize_worker(row, window, seconds) for row in rows]
        return {
            "source": "seymour-native-stratum",
            "window": window,
            "windowSeconds": seconds,
            "calculatedAt": datetime.now(UTC).isoformat(),
            "count": len(workers),
            "workers": workers,
        }

    def worker(self, worker_name: str, *, window: str = "5m") -> dict[str, Any] | None:
        seconds, since = self._window(window)
        row = self.repository.worker(worker_name=worker_name, since=since)
        return self._serialize_worker(row, window, seconds) if row else None

    def engine(self, *, window: str = "5m") -> dict[str, Any]:
        seconds, since = self._window(window)
        row = self.repository.engine(since=since)
        submissions = int(row.get("submissions") or 0)
        accepted = int(row.get("accepted") or 0)
        rejected = int(row.get("rejected") or 0)
        return {
            "source": "seymour-native-stratum",
            "window": window,
            "windowSeconds": seconds,
            "calculatedAt": datetime.now(UTC).isoformat(),
            "activeSessions": int(row.get("active_sessions") or 0),
            "connectedWorkers": int(row.get("connected_workers") or 0),
            "authorizedSessions": int(row.get("authorized_sessions") or 0),
            "submissions": submissions,
            "submissionsPerSecond": submissions / seconds,
            "accepted": accepted,
            "rejected": rejected,
            "latestSubmission": self._iso(row.get("latest_submission")),
            "messagesReceived": int(row.get("messages_received") or 0),
            "messagesSent": int(row.get("messages_sent") or 0),
            "queueDepth": None,
            "queueTelemetryAvailable": False,
        }

    def _serialize_worker(self, row: dict[str, Any], window: str, seconds: int) -> dict[str, Any]:
        accepted = int(row.get("accepted_shares") or 0)
        rejected = int(row.get("rejected_shares") or 0)
        disconnected = row.get("disconnected_at") is not None
        authorized = bool(row.get("authorized"))
        last_accepted = row.get("last_accepted_at")
        now = datetime.now(UTC)
        recent_accept = bool(last_accepted and (now - last_accepted).total_seconds() <= 120)
        hashrate = self._hashrate(float(row.get("accepted_difficulty") or 0), seconds)
        if disconnected:
            phase = "disconnected"
        elif not authorized:
            phase = "connected"
        elif accepted == 0:
            phase = "authorized"
        elif not recent_accept:
            phase = "stalled"
        elif accepted < 3:
            phase = "hashrate-stabilizing"
        else:
            phase = "stable"
        return {
            "workerName": row["worker_name"],
            "sessionId": str(row["session_id"]) if row.get("session_id") else None,
            "remoteHost": row.get("remote_host"),
            "remotePort": row.get("remote_port"),
            "window": window,
            "windowSeconds": seconds,
            "hashrate": hashrate,
            "difficulty": float(row.get("difficulty") or 0),
            "acceptedShares": accepted,
            "rejectedShares": rejected,
            "lastShareAt": self._iso(row.get("last_share_at")),
            "lastAcceptedAt": self._iso(last_accepted),
            "lastActivityAt": self._iso(row.get("last_activity_at")),
            "connectedAt": self._iso(row.get("connected_at")),
            "online": not disconnected and recent_accept,
            "phase": phase,
            **self._rates(accepted, rejected),
        }
