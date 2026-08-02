# Package 024 — Asynchronous Share Ingestion & Persistence Foundation

This package removes synchronous share validation and PostgreSQL work from the asyncio socket-reading loop and replaces per-share database connection creation with a process-wide psycopg connection pool.

## What changes

- Stratum dispatch, full share validation, session writes, duplicate checks, and submission persistence run in a bounded worker executor.
- The event loop remains available to accept, read, respond to, and close other miner connections.
- PostgreSQL connections are borrowed from a persistent connection pool rather than created for every share.
- Runtime sizing is configurable through `SEYMOUR_STRATUM_*` environment variables.
- A concurrency regression test verifies that a slow repository operation cannot starve a second Stratum client.

## Correctness

Share acknowledgements still wait for full validation and durable duplicate-aware persistence. This package does not acknowledge a share before PostgreSQL confirms insertion. It improves concurrency without weakening accounting guarantees.

## New environment settings

```text
SEYMOUR_STRATUM_PROCESSING_WORKERS=8
SEYMOUR_STRATUM_PROCESSING_QUEUE_LIMIT=2048
SEYMOUR_STRATUM_DATABASE_POOL_MIN_SIZE=2
SEYMOUR_STRATUM_DATABASE_POOL_MAX_SIZE=16
SEYMOUR_STRATUM_DATABASE_POOL_TIMEOUT_SECONDS=5
```

For the current two-Avalon test, the defaults are appropriate. Scale testing should tune worker and pool counts from measured database latency rather than guesswork.

## Installation

Run from the extracted `nexus` directory:

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```

The installer backs up replaced files under `packages/backups/024-asynchronous-share-ingestion-persistence-<timestamp>/`.
