from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class StratumSession:
    remote_host: str
    remote_port: int | None
    extranonce1: str
    extranonce2_size: int
    difficulty: float
    session_id: UUID = field(default_factory=uuid4)
    user_agent: str | None = None
    worker_name: str | None = None
    subscribed: bool = False
    authorized: bool = False
    version_rolling: bool = False
    version_rolling_mask: str | None = None
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    messages_received: int = 0
    messages_sent: int = 0
    submissions_received: int = 0
    accepted_shares: int = 0
    last_share_at: datetime | None = None
    share_interval_ewma: float | None = None
    vardiff_last_retarget_at: datetime | None = None
    vardiff_share_baseline: int = 0
    difficulty_changes: int = 0
