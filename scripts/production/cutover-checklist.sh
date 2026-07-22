#!/usr/bin/env bash
cat <<'EOF'
[ ] Seymour uses non-conflicting Stratum port 3334.
[ ] API, Stratum, PostgreSQL, and Bitcoin RPC pass health checks.
[ ] One miner uses Seymour primary and CKPool backup.
[ ] Accepted shares, VarDiff, reconnects, and hashrate are confirmed.
[ ] Bitcoin RPC interruption and recovery pass.
[ ] 24–72 hour soak passes.
[ ] Miners migrate in small batches.
[ ] CKPool remains available during rollback window.
This script does not stop CKPool or modify miners.
EOF
