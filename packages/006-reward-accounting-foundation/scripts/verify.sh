#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 006"; require_repo; load_env; PYTHON="$(python_bin)"
for f in src/seymour_pool_engine/repositories/reward_repository.py src/seymour_pool_engine/services/reward_service.py src/seymour_pool_engine/api/routes/rewards.py src/seymour_pool_engine/testing/synthetic_rewards.py; do [[ -f "$REPO_ROOT/$f" ]] || fail "$f"; done; pass "Package files"
heading "Static checks"; (cd "$REPO_ROOT" && "$PYTHON" -m ruff check src tests); pass "Ruff"
heading "Test suite"; (cd "$REPO_ROOT" && "$PYTHON" -m pytest -q); pass "Pytest"
heading "Database objects"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='$MIGRATION_ID';")" == "1" ]] || fail "Migration 007 recorded"; pass "Migration 007 recorded"
for table in reward_periods worker_reward_entries balance_ledger; do [[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='$table';")" == "1" ]] || fail "$table table"; pass "$table table"; done
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.views WHERE table_schema='seymour_engine' AND table_name='worker_balances';")" == "1" ]] || fail "Worker balances view"; pass "Worker balances view"
heading "Application import"; (cd "$REPO_ROOT" && "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app is not None'); pass "Application import"
heading "Reward API routes"
ROUTES="$(cd "$REPO_ROOT" && "$PYTHON" - <<'PY'
from seymour_pool_engine.main import app
print(*sorted(app.openapi().get("paths", {})), sep=chr(10))
PY
)"
for route in /api/v1/rewards /api/v1/rewards/balances /api/v1/rewards/calculate /api/v1/rewards/{reward_period_id}/confirm; do grep -qx "$route" <<<"$ROUTES" || fail "$route"; done; pass "Reward API routes"
printf '\nPackage 006 verified.\n'
