#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 025"
require_repo; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
PYTHON="$(python_bin)"
heading "Static checks"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests/test_ckpool_competitive_acceptance_testing.py"
pass "Ruff"
heading "Competitive acceptance tests"
"$PYTHON" -m pytest -q "$REPO_ROOT/tests/test_ckpool_competitive_acceptance_testing.py"
pass "Competitive acceptance tests"
heading "Core mining regression tests"
"$PYTHON" -m pytest -q \
 "$REPO_ROOT/tests/test_stratum_protocol.py" \
 "$REPO_ROOT/tests/test_bitcoin_template_job_engine.py" \
 "$REPO_ROOT/tests/test_share_validation_pipeline.py" \
 "$REPO_ROOT/tests/test_block_construction_submitblock.py" \
 "$REPO_ROOT/tests/test_variable_difficulty_scaling.py" \
 "$REPO_ROOT/tests/test_production_resilience_node_failover.py"
pass "Core mining regression tests"
heading "Database objects"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='026_ckpool_competitive_acceptance_testing'" | grep -qx 1 || fail "Migration 026 recorded"
pass "Migration 026 recorded"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT to_regclass('seymour_engine.acceptance_test_runs') IS NOT NULL" | grep -qx t || fail "acceptance test runs table"
pass "acceptance test runs table"
heading "Application routes"
"$PYTHON" - <<'PYROUTES'
from seymour_pool_engine.main import app
paths = set(app.openapi()["paths"])
required = {"/api/v1/acceptance/run", "/api/v1/acceptance/runs", "/api/v1/acceptance/criteria"}
missing = required - paths
assert not missing, f"Missing routes: {sorted(missing)}"
PYROUTES
pass "Acceptance API routes"
heading "Runtime acceptance"
"$PYTHON" - <<'PYRUN'
from unittest.mock import Mock
from seymour_pool_engine.services.acceptance_service import AcceptanceService
report = AcceptanceService(repository=Mock()).run(persist=False)
assert report["status"] == "passed", report
print(f"Automated acceptance: {report['checksPassed']}/{report['checksTotal']} checks passed")
PYRUN
pass "Runtime acceptance suite"
printf '\nPackage 025 verified.\n'
