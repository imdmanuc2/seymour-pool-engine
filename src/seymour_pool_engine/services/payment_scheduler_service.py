from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.payment_scheduler_repository import (
    PaymentSchedulerRepository,
)
from seymour_pool_engine.services.payout_service import PayoutService


class PaymentSchedulerService:
    SCHEDULES = {"immediate", "hourly", "daily", "weekly", "monthly", "manual"}

    def __init__(
        self,
        repository: PaymentSchedulerRepository | None = None,
        payout_service: PayoutService | None = None,
    ) -> None:
        self.repository = repository or PaymentSchedulerRepository()
        self.payout_service = payout_service or PayoutService()

    def configure_profile(self, **values: Any) -> dict[str, Any]:
        schedule_type = str(values.get("schedule_type", "daily")).lower()
        if schedule_type not in self.SCHEDULES:
            raise ValueError("Unsupported payment schedule")
        minimum = self._amount(values.get("minimum_payout", "0"), allow_zero=True)
        absolute = self._amount(values.get("absolute_minimum", "0"), allow_zero=True)
        if minimum < absolute:
            minimum = absolute
        maximum = values.get("maximum_payout")
        maximum_amount = self._amount(maximum) if maximum not in (None, "") else None
        maximum_behavior = values.get("maximum_behavior", "pay_full")
        if maximum_behavior not in {"pay_full", "cap_and_carry"}:
            raise ValueError("Unsupported maximum payout behavior")
        normalized = {
            **values,
            "coin": values["coin"].upper(),
            "network": values["network"].lower(),
            "enabled": bool(values.get("enabled", True)),
            "schedule_type": schedule_type,
            "minimum_payout": minimum,
            "absolute_minimum": absolute,
            "maximum_payout": maximum_amount,
            "maximum_behavior": maximum_behavior,
            "retry_limit": max(0, int(values.get("retry_limit", 3))),
            "retry_backoff_seconds": max(
                0, int(values.get("retry_backoff_seconds", 300))
            ),
        }
        self._validate_calendar(normalized)
        normalized["next_run_at"] = self.next_run_at(normalized, datetime.now(UTC))
        return self._profile(self.repository.upsert_profile(**normalized))

    def profiles(self, *, pool_id: str | None = None) -> list[dict[str, Any]]:
        return [self._profile(row) for row in self.repository.list_profiles(pool_id=pool_id)]

    def configure_worker_policy(self, **values: Any) -> dict[str, Any]:
        schedule = values.get("schedule_type")
        if schedule is not None:
            schedule = str(schedule).lower()
            if schedule not in self.SCHEDULES:
                raise ValueError("Unsupported worker payment schedule")
        minimum = values.get("minimum_payout")
        normalized = {
            **values,
            "coin": values["coin"].upper(),
            "network": values["network"].lower(),
            "enabled": bool(values.get("enabled", True)),
            "schedule_type": schedule,
            "minimum_payout": (
                self._amount(minimum, allow_zero=True) if minimum is not None else None
            ),
        }
        return self._worker_policy(self.repository.upsert_worker_policy(**normalized))

    def run_due(self, *, actor: str = "scheduler") -> list[dict[str, Any]]:
        results = []
        for profile in self.repository.due_profiles():
            results.append(self._execute(profile=profile, trigger_type="scheduled", actor=actor))
        return results

    def run_profile(
        self, *, scheduler_profile_id: UUID, actor: str = "api"
    ) -> dict[str, Any]:
        profile = self.repository.get_profile(scheduler_profile_id)
        if profile is None:
            raise ValueError("Payment scheduler profile was not found")
        return self._execute(profile=profile, trigger_type="manual", actor=actor)

    def runs(
        self, *, scheduler_profile_id: UUID | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        return [
            self._run(row)
            for row in self.repository.list_runs(
                scheduler_profile_id=scheduler_profile_id,
                limit=max(1, min(limit, 500)),
            )
        ]

    def jobs(self, *, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return [
            self._job(row)
            for row in self.repository.list_jobs(
                status=status, limit=max(1, min(limit, 500))
            )
        ]

    def retry_job(self, *, scheduler_job_id: UUID) -> dict[str, Any]:
        row = self.repository.transition_job(
            scheduler_job_id=scheduler_job_id,
            status="pending",
            failure_reason=None,
            next_attempt_at=datetime.now(UTC),
            increment_attempt=True,
        )
        if row is None:
            raise ValueError("Payment scheduler job cannot be retried")
        return self._job(row)

    def cancel_job(self, *, scheduler_job_id: UUID) -> dict[str, Any]:
        row = self.repository.transition_job(
            scheduler_job_id=scheduler_job_id,
            status="cancelled",
            failure_reason=None,
            next_attempt_at=None,
            increment_attempt=False,
        )
        if row is None:
            raise ValueError("Payment scheduler job cannot be cancelled")
        return self._job(row)

    def _execute(
        self, *, profile: dict[str, Any], trigger_type: str, actor: str
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        run_key = f"{profile['scheduler_profile_id']}:{trigger_type}:{now:%Y%m%d%H%M%S}"
        run = self.repository.acquire_run(
            scheduler_profile_id=profile["scheduler_profile_id"],
            run_key=run_key,
            trigger_type=trigger_type,
            actor=actor.strip() or "scheduler",
        )
        if run is None:
            raise ValueError("A payment scheduler run is already active")
        eligible_rows = self.repository.eligible_balances(profile)
        jobs: list[dict[str, Any]] = []
        skipped = 0
        for row in eligible_rows:
            decision = self.evaluate(row=row, profile=profile)
            if decision is None:
                skipped += 1
                continue
            jobs.append(
                self.repository.create_job(
                    scheduler_run_id=run["scheduler_run_id"], row=decision
                )
            )
        total = sum((Decimal(str(job["payout_amount"])) for job in jobs), Decimal("0"))
        payout_count = 0
        failure_reason = None
        if jobs:
            try:
                batch = self.payout_service.create(
                    batch_key=f"scheduler-{run['scheduler_run_id']}",
                    pool_id=profile["pool_id"],
                    coin=profile["coin"],
                    network=profile["network"],
                    source_wallet_id=profile["source_wallet_id"],
                    minimum_payout=profile["minimum_payout"],
                    requested_by=actor,
                    items=[
                        {
                            "worker_id": job.get("worker_id"),
                            "miner": job["miner"],
                            "worker": job["worker"],
                            "destination_address": job["destination_address"],
                            "amount": job["payout_amount"],
                        }
                        for job in jobs
                    ],
                    metadata={"schedulerRunId": str(run["scheduler_run_id"])},
                )
                self.repository.attach_batch(
                    scheduler_job_ids=[job["scheduler_job_id"] for job in jobs],
                    payout_batch_id=UUID(batch["payoutBatchId"]),
                )
                payout_count = len(jobs)
            except (ValueError, KeyError) as exc:
                failure_reason = str(exc)
        status = "completed" if failure_reason is None else "failed"
        finished = self.repository.finish_run(
            scheduler_run_id=run["scheduler_run_id"],
            status=status,
            eligible_count=len(eligible_rows),
            payout_count=payout_count,
            skipped_count=skipped,
            failed_count=len(jobs) if failure_reason else 0,
            total_amount=total if failure_reason is None else Decimal("0"),
            failure_reason=failure_reason,
            next_run_at=self.next_run_at(profile, now),
            actor=actor,
            metadata={"batchCreated": payout_count > 0},
        )
        return self._run(finished)

    @classmethod
    def evaluate(
        cls, *, row: dict[str, Any], profile: dict[str, Any]
    ) -> dict[str, Any] | None:
        if row.get("policy_enabled") is False or not row.get("destination_address"):
            return None
        schedule = row.get("worker_schedule_type")
        if schedule == "manual" and profile.get("schedule_type") != "manual":
            return None
        balance = Decimal(str(row["confirmed_balance"]))
        threshold = Decimal(
            str(row.get("worker_minimum_payout") or profile["minimum_payout"])
        )
        absolute = Decimal(str(profile.get("absolute_minimum", 0)))
        threshold = max(threshold, absolute)
        if balance < threshold:
            return None
        payout = balance
        maximum = profile.get("maximum_payout")
        if maximum is not None and profile.get("maximum_behavior") == "cap_and_carry":
            payout = min(balance, Decimal(str(maximum)))
        return {
            **row,
            "eligible_balance": balance,
            "threshold_amount": threshold,
            "payout_amount": payout,
            "status": "pending",
        }

    @classmethod
    def next_run_at(cls, profile: dict[str, Any], now: datetime) -> datetime | None:
        schedule = profile["schedule_type"]
        if schedule == "manual":
            return None
        if schedule == "immediate":
            return now
        if schedule == "hourly":
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        hour = int(profile.get("schedule_hour") or 0)
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if schedule == "daily":
            return candidate if candidate > now else candidate + timedelta(days=1)
        if schedule == "weekly":
            weekday = int(profile.get("schedule_weekday") or 0)
            days = (weekday - candidate.weekday()) % 7
            candidate += timedelta(days=days)
            return candidate if candidate > now else candidate + timedelta(days=7)
        monthday = int(profile.get("schedule_monthday") or 1)
        candidate = candidate.replace(day=monthday)
        if candidate > now:
            return candidate
        year = candidate.year + (1 if candidate.month == 12 else 0)
        month = 1 if candidate.month == 12 else candidate.month + 1
        return candidate.replace(year=year, month=month, day=monthday)

    @staticmethod
    def _validate_calendar(values: dict[str, Any]) -> None:
        schedule = values["schedule_type"]
        hour = values.get("schedule_hour")
        weekday = values.get("schedule_weekday")
        monthday = values.get("schedule_monthday")
        if hour is not None and not 0 <= int(hour) <= 23:
            raise ValueError("Schedule hour must be between 0 and 23")
        if schedule == "weekly" and (weekday is None or not 0 <= int(weekday) <= 6):
            raise ValueError("Weekly schedules require weekday 0 through 6")
        if schedule == "monthly" and (monthday is None or not 1 <= int(monthday) <= 28):
            raise ValueError("Monthly schedules require month day 1 through 28")

    @staticmethod
    def _amount(value: Any, *, allow_zero: bool = False) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError) as exc:
            raise ValueError("Invalid payment amount") from exc
        if amount < 0 or (amount == 0 and not allow_zero):
            raise ValueError("Payment amount must be greater than zero")
        return amount

    @staticmethod
    def _profile(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "schedulerProfileId": str(row["scheduler_profile_id"]),
            "poolId": row["pool_id"], "coin": row["coin"],
            "network": row["network"], "sourceWalletId": str(row["source_wallet_id"]),
            "enabled": row["enabled"], "scheduleType": row["schedule_type"],
            "scheduleHour": row.get("schedule_hour"),
            "scheduleWeekday": row.get("schedule_weekday"),
            "scheduleMonthday": row.get("schedule_monthday"),
            "minimumPayout": str(row["minimum_payout"]),
            "absoluteMinimum": str(row["absolute_minimum"]),
            "maximumPayout": (
                str(row["maximum_payout"]) if row.get("maximum_payout") is not None else None
            ),
            "maximumBehavior": row["maximum_behavior"],
            "retryLimit": row["retry_limit"],
            "retryBackoffSeconds": row["retry_backoff_seconds"],
            "lastRunAt": row.get("last_run_at").isoformat() if row.get("last_run_at") else None,
            "nextRunAt": row.get("next_run_at").isoformat() if row.get("next_run_at") else None,
        }

    @staticmethod
    def _worker_policy(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "workerPaymentPolicyId": str(row["worker_payment_policy_id"]),
            "workerId": str(row["worker_id"]), "coin": row["coin"],
            "network": row["network"], "enabled": row["enabled"],
            "minimumPayout": (
                str(row["minimum_payout"]) if row.get("minimum_payout") is not None else None
            ),
            "scheduleType": row.get("schedule_type"),
            "destinationWalletId": (
                str(row["destination_wallet_id"])
                if row.get("destination_wallet_id") else None
            ),
        }

    @staticmethod
    def _run(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "schedulerRunId": str(row["scheduler_run_id"]),
            "schedulerProfileId": str(row["scheduler_profile_id"]),
            "runKey": row["run_key"], "triggerType": row["trigger_type"],
            "status": row["status"], "actor": row["actor"],
            "eligibleCount": row["eligible_count"],
            "payoutCount": row["payout_count"],
            "skippedCount": row["skipped_count"],
            "failedCount": row["failed_count"],
            "totalAmount": str(row["total_amount"]),
            "failureReason": row.get("failure_reason"),
            "startedAt": row["started_at"].isoformat(),
            "completedAt": row.get("completed_at").isoformat() if row.get("completed_at") else None,
        }

    @staticmethod
    def _job(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "schedulerJobId": str(row["scheduler_job_id"]),
            "schedulerRunId": str(row["scheduler_run_id"]),
            "workerId": str(row["worker_id"]) if row.get("worker_id") else None,
            "payoutBatchId": (
                str(row["payout_batch_id"]) if row.get("payout_batch_id") else None
            ),
            "poolId": row["pool_id"], "miner": row["miner"],
            "worker": row["worker"], "destinationAddress": row["destination_address"],
            "eligibleBalance": str(row["eligible_balance"]),
            "thresholdAmount": str(row["threshold_amount"]),
            "payoutAmount": str(row["payout_amount"]), "status": row["status"],
            "attemptCount": row["attempt_count"],
            "nextAttemptAt": (
                row.get("next_attempt_at").isoformat() if row.get("next_attempt_at") else None
            ),
            "failureReason": row.get("failure_reason"),
        }
