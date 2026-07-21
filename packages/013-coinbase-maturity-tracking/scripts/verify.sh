#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 013"; require_repo; load_env
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file missing"; pass "Package files"
heading "Static checks"; PYTHON="$(python_bin)"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"; pass "Ruff"
heading "Test suite"; "$PYTHON" -m pytest -q "$REPO_ROOT/tests"; pass "Pytest"
heading "Database objects"
for check in   "Migration 014 recorded|SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='014_coinbase_maturity_tracking'"   "coinbase_maturity_policies table|SELECT to_regclass('seymour_engine.coinbase_maturity_policies') IS NOT NULL"   "coinbase_maturity_records table|SELECT to_regclass('seymour_engine.coinbase_maturity_records') IS NOT NULL"   "coinbase_maturity_events table|SELECT to_regclass('seymour_engine.coinbase_maturity_events') IS NOT NULL"   "maturity block uniqueness|SELECT COUNT(*) > 0 FROM pg_constraint WHERE conrelid='seymour_engine.coinbase_maturity_records'::regclass AND contype='u'"   "default BTC maturity policy|SELECT required_confirmations=100 FROM seymour_engine.coinbase_maturity_policies WHERE coin='BTC' AND network='mainnet'"
do
  label="${check%%|*}"; sql="${check#*|}"
  result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"
  [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"; pass "$label"
done
heading "Application import"
"$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'; pass "Application import"
heading "Coinbase maturity API routes"
"$PYTHON" - <<'PYTHON'
from seymour_pool_engine.main import app
paths = set(app.openapi()["paths"])
required = {
    "/api/v1/coinbase-maturity/policies",
    "/api/v1/coinbase-maturity/policies/{coin}/{network}",
    "/api/v1/coinbase-maturity/observations",
    "/api/v1/coinbase-maturity/records",
    "/api/v1/coinbase-maturity/summary",
}
missing = required - paths
assert not missing, f"Missing maturity API routes: {sorted(missing)}"
PYTHON
pass "Coinbase maturity API routes"
printf '
Package 013 verified.
'
