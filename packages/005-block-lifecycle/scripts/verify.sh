#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 005"; require_repo; load_env; PYTHON="$(python_bin)"
for f in src/seymour_pool_engine/repositories/block_repository.py src/seymour_pool_engine/services/block_service.py src/seymour_pool_engine/api/routes/blocks.py src/seymour_pool_engine/testing/synthetic_blocks.py; do [[ -f "$REPO_ROOT/$f" ]] || fail "$f"; done; pass "Package files"
heading "Static checks"; (cd "$REPO_ROOT" && "$PYTHON" -m ruff check src tests); pass "Ruff"
heading "Test suite"; (cd "$REPO_ROOT" && "$PYTHON" -m pytest -q); pass "Pytest"
heading "Database objects"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='$MIGRATION_ID';")" == "1" ]] || fail "Migration 006 recorded"; pass "Migration 006 recorded"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='blocks';")" == "1" ]] || fail "Blocks table"; pass "Blocks table"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='block_events';")" == "1" ]] || fail "Block events table"; pass "Block events table"
heading "Application import"; (cd "$REPO_ROOT" && "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app is not None'); pass "Application import"
heading "Block API routes"
ROUTES="$(cd "$REPO_ROOT" && "$PYTHON" - <<'PY'
from seymour_pool_engine.main import app
print(*sorted(app.openapi().get("paths", {})), sep=chr(10))
PY
)"
for route in /api/v1/blocks /api/v1/blocks/statistics /api/v1/blocks/{block_id} /api/v1/blocks/sync; do grep -qx "$route" <<<"$ROUTES" || fail "$route"; done; pass "Block API routes"
printf '\nPackage 005 verified.\n'
