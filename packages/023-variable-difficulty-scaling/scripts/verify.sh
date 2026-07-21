#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 023"
require_repo; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
PYTHON="$(python_bin)"
heading "Static checks"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests/test_variable_difficulty_scaling.py"
pass "Ruff"
heading "Variable difficulty tests"
"$PYTHON" -m pytest -q "$REPO_ROOT/tests/test_variable_difficulty_scaling.py"
pass "Variable difficulty tests"
heading "Database objects"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='024_variable_difficulty_scaling'" | grep -qx 1 || fail "Migration 024 recorded"
pass "Migration 024 recorded"
for column in accepted_shares last_share_at share_interval_ewma vardiff_last_retarget_at vardiff_share_baseline difficulty_changes; do
 psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1 FROM information_schema.columns WHERE table_schema='seymour_engine' AND table_name='stratum_sessions' AND column_name='$column'" | grep -qx 1 || fail "stratum_sessions.$column"
 pass "stratum_sessions.$column"
done
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT to_regclass('seymour_engine.stratum_difficulty_history') IS NOT NULL" | grep -qx t || fail "difficulty history table"
pass "difficulty history table"
heading "Application routes"
"$PYTHON" - <<'PYROUTES'
from seymour_pool_engine.main import app
paths = set(app.openapi()["paths"])
required = {"/api/v1/vardiff/status", "/api/v1/vardiff/history"}
missing = required - paths
assert not missing, f"Missing routes: {sorted(missing)}"
PYROUTES
pass "VarDiff API routes"
heading "Runtime imports"
"$PYTHON" - <<'PYIMPORTS'
from seymour_pool_engine.engines.vardiff import VarDiffController
from seymour_pool_engine.services.vardiff_service import VarDiffService
assert VarDiffController and VarDiffService
PYIMPORTS
pass "VarDiff runtime imports"
printf '\nPackage 023 verified.\n'
