# Package 008 — Health Monitoring & Alerts

Adds persistent health observations and an operational alert lifecycle to Seymour Pool Engine.

## Capabilities

- Collect engine and MiningCore health observations
- Persist health history
- Open or update warning and critical alerts
- Automatically resolve active alerts when components recover
- Acknowledge alerts
- Suppress alerts through a future timestamp with an audit reason
- Persist alert lifecycle events
- Query alerts and observation history through the API

## Install

```bash
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```
