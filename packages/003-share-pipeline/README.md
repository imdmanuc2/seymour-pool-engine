# Package 003 — Share Pipeline Foundation

Adds durable, idempotent share ingestion to Seymour Pool Engine.

## Capabilities

- SPE-owned `seymour_engine.shares` ledger
- MiningCore share retrieval
- Deterministic provider share keys
- Duplicate-safe ingestion
- Worker association when inventory identity is available
- Filtered share query API
- Manual share synchronization API

## API

- `GET /api/v1/shares`
- `POST /api/v1/shares/sync`

## Install

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```

The MiningCore database URL is optional for installation and verification, but it is required for live synchronization.
