#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 017"; require_repo; load_env
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file missing"; pass "Package files"
heading "Static checks"; PYTHON="$(python_bin)"; "$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"; pass "Ruff"
heading "Test suite"; "$PYTHON" -m pytest -q "$REPO_ROOT/tests"; pass "Pytest"
heading "Database objects"
for check in \
"Migration 018 recorded|SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='018_reliability_backup_disaster_recovery'" \
"backup profiles table|SELECT to_regclass('seymour_engine.backup_profiles') IS NOT NULL" \
"backup targets table|SELECT to_regclass('seymour_engine.backup_targets') IS NOT NULL" \
"backup runs table|SELECT to_regclass('seymour_engine.backup_runs') IS NOT NULL" \
"backup artifacts table|SELECT to_regclass('seymour_engine.backup_artifacts') IS NOT NULL" \
"integrity checks table|SELECT to_regclass('seymour_engine.backup_integrity_checks') IS NOT NULL" \
"restore runs table|SELECT to_regclass('seymour_engine.restore_runs') IS NOT NULL" \
"health snapshots table|SELECT to_regclass('seymour_engine.health_snapshots') IS NOT NULL" \
"DR playbooks table|SELECT to_regclass('seymour_engine.disaster_recovery_playbooks') IS NOT NULL" \
"backup events table|SELECT to_regclass('seymour_engine.backup_events') IS NOT NULL" \
"default profiles seeded|SELECT COUNT(*) >= 3 FROM seymour_engine.backup_profiles"
do label="${check%%|*}"; sql="${check#*|}"; result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"; [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"; pass "$label"; done
heading "Application import"; "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'; pass "Application import"
heading "Reliability API routes"; "$PYTHON" - <<'PY'
from seymour_pool_engine.main import app
paths=set(app.openapi()["paths"])
required={"/api/v1/reliability/backup-profiles","/api/v1/reliability/backup-targets","/api/v1/reliability/backup-runs","/api/v1/reliability/disaster-recovery-playbooks"}
assert not required-paths, sorted(required-paths)
PY
pass "Reliability API routes"; printf '\nPackage 017 verified.\n'
