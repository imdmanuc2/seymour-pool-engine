#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 004"; require_repo; load_env; PYTHON="$(python_bin)"
for f in src/seymour_pool_engine/repositories/statistics_repository.py src/seymour_pool_engine/services/statistics_service.py src/seymour_pool_engine/api/routes/statistics.py src/seymour_pool_engine/testing/synthetic_shares.py; do [[ -f "$REPO_ROOT/$f" ]] || fail "$f"; done; pass "Package files"
heading "Static checks"; (cd "$REPO_ROOT" && "$PYTHON" -m ruff check src tests); pass "Ruff"
heading "Test suite"; (cd "$REPO_ROOT" && "$PYTHON" -m pytest -q); pass "Pytest"
heading "Database objects"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='$MIGRATION_ID';")" == "1" ]] || fail "Migration 005 recorded"; pass "Migration 005 recorded"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='statistics_snapshots';")" == "1" ]] || fail "Statistics snapshots table"; pass "Statistics snapshots table"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='seymour_engine' AND table_name='shares' AND column_name='share_status';")" == "1" ]] || fail "Share status column"; pass "Share status column"
heading "Application import"; (cd "$REPO_ROOT" && "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app is not None'); pass "Application import"
heading "Statistics API routes"
ROUTES="$(cd "$REPO_ROOT" && "$PYTHON" - <<'PY'
from seymour_pool_engine.main import app
print(*sorted(app.openapi().get("paths", {})), sep=chr(10))
PY
)"
for route in /api/v1/statistics/overview /api/v1/statistics/pools /api/v1/statistics/workers; do grep -qx "$route" <<<"$ROUTES" || fail "$route"; done; pass "Statistics API routes"
printf '\nPackage 004 verified.\n'
