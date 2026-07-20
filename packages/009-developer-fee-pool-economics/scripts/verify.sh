#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 009"; require_repo; load_env; PYTHON="$(python_bin)"
for f in src/seymour_pool_engine/repositories/economics_repository.py src/seymour_pool_engine/services/economics_service.py src/seymour_pool_engine/api/routes/economics.py; do [[ -f "$REPO_ROOT/$f" ]] || fail "$f"; done; pass "Package files"
heading "Static checks"; (cd "$REPO_ROOT" && "$PYTHON" -m ruff check src tests); pass "Ruff"
heading "Test suite"; (cd "$REPO_ROOT" && "$PYTHON" -m pytest -q); pass "Pytest"
heading "Database objects"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='$MIGRATION_ID';")" == "1" ]] || fail "Migration 010 recorded"; pass "Migration 010 recorded"
for table in fee_profiles reward_calculations reward_allocations reward_calculation_events; do [[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='$table';")" == "1" ]] || fail "$table table"; pass "$table table"; done
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='ck_developer_fee_minimum';" | grep -c '0.7500')" -ge 1 ]] || fail "Mandatory 0.75 percent constraint"; pass "Mandatory 0.75 percent constraint"
heading "Application import"; (cd "$REPO_ROOT" && "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app is not None'); pass "Application import"
heading "Economics API routes"; ROUTES="$(cd "$REPO_ROOT" && "$PYTHON" - <<'PY2'
from seymour_pool_engine.main import app
print(*sorted(app.openapi().get("paths", {})), sep=chr(10))
PY2
)"; for route in /api/v1/economics/fees /api/v1/economics/calculations /api/v1/economics/summary /api/v1/economics/policy; do grep -qx "$route" <<<"$ROUTES" || fail "$route"; done; pass "Economics API routes"
printf '
Package 009 verified.
'
