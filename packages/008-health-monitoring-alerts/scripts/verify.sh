#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 008"; require_repo; load_env; PYTHON="$(python_bin)"
for f in src/seymour_pool_engine/repositories/health_monitoring_repository.py src/seymour_pool_engine/services/health_monitoring_service.py src/seymour_pool_engine/api/routes/monitoring.py; do [[ -f "$REPO_ROOT/$f" ]] || fail "$f"; done; pass "Package files"
heading "Static checks"; (cd "$REPO_ROOT" && "$PYTHON" -m ruff check src tests); pass "Ruff"
heading "Test suite"; (cd "$REPO_ROOT" && "$PYTHON" -m pytest -q); pass "Pytest"
heading "Database objects"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='$MIGRATION_ID';")" == "1" ]] || fail "Migration 009 recorded"; pass "Migration 009 recorded"
for table in health_observations alert_rules alerts alert_events; do [[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='$table';")" == "1" ]] || fail "$table table"; pass "$table table"; done
heading "Application import"; (cd "$REPO_ROOT" && "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app is not None'); pass "Application import"
heading "Monitoring API routes"
ROUTES="$(cd "$REPO_ROOT" && "$PYTHON" - <<'PY'
from seymour_pool_engine.main import app
print(*sorted(app.openapi().get("paths", {})), sep=chr(10))
PY
)"
for route in /api/v1/monitoring/health/collect /api/v1/monitoring/health/observations /api/v1/monitoring/alerts; do grep -qx "$route" <<<"$ROUTES" || fail "$route"; done; pass "Monitoring API routes"
printf '\nPackage 008 verified.\n'
