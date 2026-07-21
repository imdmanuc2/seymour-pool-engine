#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 012"; require_repo; load_env
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file missing"; pass "Package files"
heading "Static checks"; PYTHON="$(python_bin)"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"; pass "Ruff"
heading "Test suite"; "$PYTHON" -m pytest -q "$REPO_ROOT/tests"; pass "Pytest"
heading "Database objects"
for check in \
  "Migration 013 recorded|SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='013_payout_engine'" \
  "payout_batches table|SELECT to_regclass('seymour_engine.payout_batches') IS NOT NULL" \
  "payout_items table|SELECT to_regclass('seymour_engine.payout_items') IS NOT NULL" \
  "payout_events table|SELECT to_regclass('seymour_engine.payout_events') IS NOT NULL" \
  "batch key uniqueness|SELECT COUNT(*) > 0 FROM pg_constraint WHERE conrelid='seymour_engine.payout_batches'::regclass AND contype='u'"
do
  label="${check%%|*}"; sql="${check#*|}"
  result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"
  [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"; pass "$label"
done
heading "Application import"; "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'; pass "Application import"
heading "Payout API routes"
"$PYTHON" - <<'PYTHON'
from seymour_pool_engine.main import app
paths = set(app.openapi()["paths"])
required = {
    "/api/v1/payouts/eligible", "/api/v1/payouts/batches",
    "/api/v1/payouts/batches/{payout_batch_id}",
    "/api/v1/payouts/batches/{payout_batch_id}/approve",
    "/api/v1/payouts/batches/{payout_batch_id}/complete",
}
missing = required - paths
assert not missing, f"Missing payout API routes: {sorted(missing)}"
PYTHON
pass "Payout API routes"
printf '\nPackage 012 verified.\n'
