from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import exp


@dataclass(frozen=True, slots=True)
class VarDiffConfig:
    target_share_seconds: float = 15.0
    retarget_interval_seconds: float = 90.0
    min_difficulty: float = 1.0
    max_difficulty: float = 1_000_000_000.0
    variance_percent: float = 30.0
    damping: float = 0.5
    max_step_factor: float = 4.0
    ewma_alpha: float = 0.35
    minimum_samples: int = 4


@dataclass(frozen=True, slots=True)
class VarDiffDecision:
    changed: bool
    old_difficulty: float
    new_difficulty: float
    observed_share_seconds: float | None
    reason: str


@dataclass(slots=True)
class VarDiffController:
    config: VarDiffConfig = field(default_factory=VarDiffConfig)

    def observe(self, session, observed_at: datetime | None = None) -> VarDiffDecision:
        now = observed_at or datetime.now(UTC)
        previous = session.last_share_at
        session.last_share_at = now
        session.accepted_shares += 1

        if previous is None:
            session.vardiff_last_retarget_at = session.vardiff_last_retarget_at or now
            return VarDiffDecision(
                False, session.difficulty, session.difficulty, None, "first-share"
            )

        interval = max((now - previous).total_seconds(), 0.001)
        if session.share_interval_ewma is None:
            session.share_interval_ewma = interval
        else:
            alpha = self.config.ewma_alpha
            session.share_interval_ewma = (
                alpha * interval + (1.0 - alpha) * session.share_interval_ewma
            )

        last_retarget = session.vardiff_last_retarget_at or session.connected_at
        elapsed = (now - last_retarget).total_seconds()
        samples = session.accepted_shares - session.vardiff_share_baseline
        if samples < self.config.minimum_samples:
            return VarDiffDecision(
                False,
                session.difficulty,
                session.difficulty,
                session.share_interval_ewma,
                "insufficient-samples",
            )
        if elapsed < self.config.retarget_interval_seconds:
            return VarDiffDecision(
                False,
                session.difficulty,
                session.difficulty,
                session.share_interval_ewma,
                "retarget-interval",
            )

        observed = session.share_interval_ewma
        target = self.config.target_share_seconds
        low = target * (1.0 - self.config.variance_percent / 100.0)
        high = target * (1.0 + self.config.variance_percent / 100.0)
        if low <= observed <= high:
            session.vardiff_last_retarget_at = now
            session.vardiff_share_baseline = session.accepted_shares
            return VarDiffDecision(
                False, session.difficulty, session.difficulty, observed, "within-variance"
            )

        raw_factor = target / observed
        bounded = min(
            self.config.max_step_factor,
            max(
                1.0 / self.config.max_step_factor,
                raw_factor,
            ),
        )
        damped = exp(self.config.damping * __import__("math").log(bounded))
        old = float(session.difficulty)

        session_minimum = max(
            1e-8,
            float(
                getattr(
                    session,
                    "minimum_difficulty",
                    self.config.min_difficulty,
                )
            ),
        )

        new = min(
            self.config.max_difficulty,
            max(
                session_minimum,
                old * damped,
            ),
        )
        new = max(
            session_minimum,
            round(new, 8),
        )

        session.vardiff_last_retarget_at = now
        session.vardiff_share_baseline = session.accepted_shares
        if abs(new - old) < max(1e-8, old * 0.001):
            return VarDiffDecision(False, old, old, observed, "change-too-small")

        session.difficulty = new
        session.difficulty_changes += 1
        return VarDiffDecision(True, old, new, observed, "retargeted")
