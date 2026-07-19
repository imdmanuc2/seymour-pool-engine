#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

heading "Verify Package 001B"
require_repo
load_env
PYTHON="$(python_bin)"

[[ -f "$REPO_ROOT/src/seymour_pool_engine/providers/base.py" ]] \
  || fail "Provider interface"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/providers/miningcore/provider.py" ]] \
  || fail "MiningCore provider"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/api/routes/miningcore.py" ]] \
  || fail "MiningCore API routes"
pass "Package files"

heading "Static checks"
(
  cd "$REPO_ROOT"
  "$PYTHON" -m ruff check .
)
pass "Ruff"

heading "Test suite"
(
  cd "$REPO_ROOT"
  "$PYTHON" -m pytest
)
pass "Pytest"

heading "Migration"
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
MIGRATION_COUNT="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc \
  "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id = '$MIGRATION_ID';")"
[[ "$MIGRATION_COUNT" == "1" ]] || fail "Migration 002 recorded"
pass "Migration 002 recorded"

heading "Python import"
(
  cd "$REPO_ROOT"
  "$PYTHON" -c 'from seymour_pool_engine.main import app; assert app is not None'
)
pass "Application import"

if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^seymour-pool-engine.service'; then
  systemctl is-active --quiet seymour-pool-engine.service || fail "Engine service"
  pass "Engine service"
fi

printf '\nPackage 001B verified.\n'
