# Package 024 — Production Resilience & Node Failover

Adds ordered multi-node Bitcoin Core RPC failover to the native mining path.

## Capabilities

- Comma-separated RPC endpoint configuration through `SEYMOUR_BITCOIN_RPC_URLS`.
- Automatic retry against alternate Bitcoin Core nodes.
- Per-endpoint failure counters and circuit breakers.
- Cooldown-based recovery and return to a recovered node.
- Shared resilient RPC client used by template generation and block submission.
- Node status, active endpoint, probe, and failover-history APIs.
- Persistent operational events in PostgreSQL.

The existing `SEYMOUR_BITCOIN_RPC_URL` remains supported as the single-node fallback.
