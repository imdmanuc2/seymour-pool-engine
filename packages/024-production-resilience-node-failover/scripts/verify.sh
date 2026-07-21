#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 024"
require_repo; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
PYTHON="$(python_bin)"
heading "Static checks"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests/test_production_resilience_node_failover.py"
pass "Ruff"
heading "Production resilience tests"
"$PYTHON" -m pytest -q "$REPO_ROOT/tests/test_production_resilience_node_failover.py"
pass "Production resilience tests"
heading "Database objects"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='025_production_resilience_node_failover'" | grep -qx 1 || fail "Migration 025 recorded"
pass "Migration 025 recorded"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT to_regclass('seymour_engine.bitcoin_rpc_failover_events') IS NOT NULL" | grep -qx t || fail "failover events table"
pass "failover events table"
heading "Application routes"
"$PYTHON" - <<'PYROUTES'
from seymour_pool_engine.main import app
paths = set(app.openapi()["paths"])
required = {
    "/api/v1/bitcoin/nodes/status",
    "/api/v1/bitcoin/nodes/probe",
    "/api/v1/bitcoin/nodes/failover-history",
}
missing = required - paths
assert not missing, f"Missing routes: {sorted(missing)}"
PYROUTES
pass "Node failover API routes"
heading "Runtime imports"
"$PYTHON" - <<'PYIMPORTS'
from seymour_pool_engine.providers.bitcoin import ResilientBitcoinRpcClient
from seymour_pool_engine.services.node_failover_service import NodeFailoverService
assert ResilientBitcoinRpcClient and NodeFailoverService
PYIMPORTS
pass "Node failover runtime imports"
printf '\nPackage 024 verified.\n'
