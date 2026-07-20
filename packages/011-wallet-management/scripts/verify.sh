#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 011"
require_repo; load_env
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file missing"
pass "Package files"
heading "Static checks"
PYTHON="$(python_bin)"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"
pass "Ruff"
heading "Test suite"
"$PYTHON" -m pytest -q "$REPO_ROOT/tests"
pass "Pytest"
heading "Database objects"
for check in \
  "Migration 012 recorded|SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='012_wallet_management'" \
  "wallets table|SELECT to_regclass('seymour_engine.wallets') IS NOT NULL" \
  "wallet_events table|SELECT to_regclass('seymour_engine.wallet_events') IS NOT NULL" \
  "worker_payout_addresses table|SELECT to_regclass('seymour_engine.worker_payout_addresses') IS NOT NULL" \
  "developer wallet uniqueness|SELECT to_regclass('seymour_engine.uq_active_developer_wallet_per_coin_network') IS NOT NULL"
do
  label="${check%%|*}"; sql="${check#*|}"
  result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"
  [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"
  pass "$label"
done
heading "Application import"
"$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'
pass "Application import"
heading "Wallet API routes"
"$PYTHON" - <<'PYTHON'
from seymour_pool_engine.main import app

paths = set(app.openapi()["paths"])

required_paths = {
    "/api/v1/wallets",
    "/api/v1/wallets/{wallet_id}",
    "/api/v1/workers/{worker_id}/payout-addresses/{coin}",
}

missing = required_paths - paths
assert not missing, f"Missing wallet API routes: {sorted(missing)}"
PYTHON
pass "Wallet API routes"

