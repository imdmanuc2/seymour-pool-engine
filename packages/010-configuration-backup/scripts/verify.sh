#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 010"; require_repo; load_env; PYTHON="$(python_bin)"
for f in \
  src/seymour_pool_engine/repositories/configuration_repository.py \
  src/seymour_pool_engine/services/configuration_service.py \
  src/seymour_pool_engine/api/routes/configuration.py; do
  [[ -f "$REPO_ROOT/$f" ]] || fail "$f"
done
pass "Package files"
heading "Static checks"; (cd "$REPO_ROOT" && "$PYTHON" -m ruff check src tests); pass "Ruff"
heading "Test suite"; (cd "$REPO_ROOT" && "$PYTHON" -m pytest -q); pass "Pytest"
heading "Database objects"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='$MIGRATION_ID';")" == "1" ]] || fail "Migration 011 recorded"
pass "Migration 011 recorded"
for table in configuration_profiles configuration_revisions configuration_validation_results configuration_exports configuration_imports; do
  [[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='$table';")" == "1" ]] || fail "$table table"
  pass "$table table"
done
heading "Application import"; (cd "$REPO_ROOT" && "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app is not None'); pass "Application import"
heading "Configuration API routes"
ROUTES="$(cd "$REPO_ROOT" && "$PYTHON" - <<'PY2'
from seymour_pool_engine.main import app
print(*sorted(app.openapi().get("paths", {})), sep=chr(10))
PY2
)"
for route in /api/v1/config /api/v1/config/validate /api/v1/config/history /api/v1/config/export /api/v1/config/import '/api/v1/config/rollback/{revision_number}'; do
  grep -Fxq "$route" <<<"$ROUTES" || fail "$route"
done
pass "Configuration API routes"
printf '\nPackage 010 verified.\n'
