#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 018"; require_repo; load_env
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file missing"; pass "Package files"
heading "Static checks"; PYTHON="$(python_bin)"; "$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"; pass "Ruff"
heading "Test suite"; "$PYTHON" -m pytest -q "$REPO_ROOT/tests"; pass "Pytest"
heading "Database objects"
for check in "Migration 019 recorded|SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='019_nexus_integration_release_readiness'" "integration clients table|SELECT to_regclass('seymour_engine.integration_clients') IS NOT NULL" "integration commands table|SELECT to_regclass('seymour_engine.integration_commands') IS NOT NULL" "integration events table|SELECT to_regclass('seymour_engine.integration_events') IS NOT NULL" "compatibility matrix table|SELECT to_regclass('seymour_engine.compatibility_matrix') IS NOT NULL" "release validations table|SELECT to_regclass('seymour_engine.release_validations') IS NOT NULL" "release checklist table|SELECT to_regclass('seymour_engine.release_checklists') IS NOT NULL" "Nexus client seeded|SELECT COUNT(*) >= 1 FROM seymour_engine.integration_clients WHERE client_key='nexus-command-center'"; do label="${check%%|*}"; sql="${check#*|}"; result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"; [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"; pass "$label"; done
heading "Application import"; "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'; pass "Application import"
heading "Nexus integration API routes"; "$PYTHON" -c 'from seymour_pool_engine.main import app; p=set(app.openapi()["paths"]); r={"/api/v1/version","/api/v1/integration/status","/api/v1/integration/summary","/api/v1/release/readiness","/api/v1/integration/commands"}; assert not r-p, sorted(r-p)'
pass "Nexus integration API routes"; printf '\nPackage 018 verified.\n'
