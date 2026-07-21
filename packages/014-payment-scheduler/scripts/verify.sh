#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 014"; require_repo; load_env
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file missing"; pass "Package files"
heading "Static checks"; PYTHON="$(python_bin)"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"; pass "Ruff"
heading "Test suite"; "$PYTHON" -m pytest -q "$REPO_ROOT/tests"; pass "Pytest"
heading "Database objects"
for check in \
  "Migration 015 recorded|SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='015_payment_scheduler'" \
  "scheduler profiles table|SELECT to_regclass('seymour_engine.payment_scheduler_profiles') IS NOT NULL" \
  "worker payment policies table|SELECT to_regclass('seymour_engine.worker_payment_policies') IS NOT NULL" \
  "scheduler runs table|SELECT to_regclass('seymour_engine.payment_scheduler_runs') IS NOT NULL" \
  "scheduler jobs table|SELECT to_regclass('seymour_engine.payment_scheduler_jobs') IS NOT NULL" \
  "scheduler events table|SELECT to_regclass('seymour_engine.payment_scheduler_events') IS NOT NULL" \
  "active run uniqueness|SELECT COUNT(*) > 0 FROM pg_indexes WHERE schemaname='seymour_engine' AND indexname='uq_payment_scheduler_active_run'"
do
  label="${check%%|*}"; sql="${check#*|}"
  result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"
  [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"; pass "$label"
done
heading "Application import"
"$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'; pass "Application import"
heading "Payment scheduler API routes"
"$PYTHON" - <<'PYTHON'
from seymour_pool_engine.main import app
paths = set(app.openapi()["paths"])
required = {
    "/api/v1/payment-scheduler/profiles",
    "/api/v1/payment-scheduler/worker-policies",
    "/api/v1/payment-scheduler/run-due",
    "/api/v1/payment-scheduler/profiles/{scheduler_profile_id}/run",
    "/api/v1/payment-scheduler/runs",
    "/api/v1/payment-scheduler/jobs",
    "/api/v1/payment-scheduler/jobs/{scheduler_job_id}/retry",
    "/api/v1/payment-scheduler/jobs/{scheduler_job_id}/cancel",
}
missing = required - paths
assert not missing, f"Missing payment scheduler API routes: {sorted(missing)}"
PYTHON
pass "Payment scheduler API routes"
printf '\nPackage 014 verified.\n'
