#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

heading "Verify Package 003"
require_repo
load_env
PYTHON="$(python_bin)"

[[ -f "$REPO_ROOT/src/seymour_pool_engine/repositories/share_repository.py" ]] \
  || fail "Share repository"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/services/share_service.py" ]] \
  || fail "Share service"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/api/routes/shares.py" ]] \
  || fail "Share API"
pass "Package files"

heading "Static checks"
(cd "$REPO_ROOT" && "$PYTHON" -m ruff check src tests)
pass "Ruff"

heading "Test suite"
(cd "$REPO_ROOT" && "$PYTHON" -m pytest -q)
pass "Pytest"

heading "Database objects"
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
MIGRATION_COUNT="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc \
  "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id = '$MIGRATION_ID';")"
[[ "$MIGRATION_COUNT" == "1" ]] || fail "Migration 004 recorded"
pass "Migration 004 recorded"

TABLE_COUNT="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='shares';")"
[[ "$TABLE_COUNT" == "1" ]] || fail "Shares table"
pass "Shares table"

INDEX_COUNT="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc \
  "SELECT COUNT(*) FROM pg_indexes WHERE schemaname='seymour_engine' AND indexname IN ('idx_shares_pool_created','idx_shares_worker_created','idx_shares_provider_created');")"
[[ "$INDEX_COUNT" == "3" ]] || fail "Share indexes"
pass "Share indexes"

heading "Application import"
(cd "$REPO_ROOT" && "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app is not None')
pass "Application import"

heading "Share API routes"
ROUTES="$(cd "$REPO_ROOT" && "$PYTHON" - <<'ROUTES_PY'
from seymour_pool_engine.main import app

paths = sorted(app.openapi().get("paths", {}))
print(*paths, sep=chr(10))
ROUTES_PY
)"
grep -qx '/api/v1/shares' <<<"$ROUTES" || fail "GET /api/v1/shares"
grep -qx '/api/v1/shares/sync' <<<"$ROUTES" || fail "POST /api/v1/shares/sync"
pass "Share API routes"

if command -v systemctl >/dev/null 2>&1 \
  && systemctl list-unit-files 2>/dev/null | grep -q '^seymour-pool-engine.service'; then
  systemctl is-active --quiet seymour-pool-engine.service || fail "Engine service"
  pass "Engine service"
fi

printf '\nPackage 003 verified.\n'
