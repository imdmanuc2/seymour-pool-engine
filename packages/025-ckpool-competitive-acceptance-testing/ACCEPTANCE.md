# Acceptance criteria

Package installation passes when migration 026 is recorded, the report table exists, all new tests pass, the native mining regression suite passes, API contracts are present, and the runtime acceptance report is `passed`.

Production release still requires an external soak test with real Bitcoin Core, representative ASICs, planned failover, and a same-hardware CKPool comparison. Record latency, accepted/rejected shares, disconnects, stale shares, CPU/memory use, template age, and recovery time.
