# Package 002 — Worker Inventory and Lifecycle

This package makes Seymour Pool Engine the owner of persistent worker state instead of exposing MiningCore worker rows directly.

It adds:

- `seymour_engine.workers`
- provider-to-worker identity reconciliation
- active/offline lifecycle state
- first seen, last seen, provider observation, and synchronization timestamps
- SPE-owned `GET /api/v1/workers`
- explicit `POST /api/v1/workers/sync`
- repository, service, API, and tests

## Install

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```

## First synchronization

```bash
curl -X POST http://127.0.0.1:8561/api/v1/workers/sync
curl http://127.0.0.1:8561/api/v1/workers
```

The active window defaults to 300 seconds and can be changed with:

```bash
SEYMOUR_WORKER_ACTIVE_WINDOW_SECONDS=300
```
