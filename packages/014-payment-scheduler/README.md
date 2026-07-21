# Package 014 — Payment Scheduler

Completes automated payout scheduling for Seymour Pool Engine.

## Capabilities

- Per-pool and per-coin scheduler profiles
- Configurable minimum and absolute payout thresholds
- Optional per-worker threshold and schedule overrides
- Immediate, hourly, daily, weekly, monthly, and manual schedules
- Single-active-run execution lock
- Payout batch creation through the existing payout engine
- Run history, jobs, retry, cancellation, and audit events
- Optional maximum payout cap-and-carry behavior

## Install

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```
