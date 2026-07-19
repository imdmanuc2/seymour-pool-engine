#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

heading "Package 003 doctor"
require_repo
pass "Repository detected"

[[ -d "$PAYLOAD_DIR" ]] || fail "Package payload"
[[ -f "$PAYLOAD_DIR/migrations/004_share_pipeline.sql" ]] || fail "Share migration"
pass "Package payload"

PYTHON="$(python_bin)"
"$PYTHON" --version >/dev/null
pass "Python runtime"

[[ -f "$REPO_ROOT/.env" ]] || fail ".env configuration file"
pass ".env configuration file"

load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
pass "Engine database URL"

command -v psql >/dev/null 2>&1 || fail "PostgreSQL client"
pass "PostgreSQL client"

psql "$SEYMOUR_ENGINE_DATABASE_URL" -v ON_ERROR_STOP=1 -Atqc 'SELECT 1' >/dev/null \
  || fail "Engine database connection"
pass "Engine database connection"

WORKERS_COUNT="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='seymour_engine' AND table_name='workers';")"
[[ "$WORKERS_COUNT" == "1" ]] || fail "Package 002 worker lifecycle"
pass "Package 002 worker lifecycle"

if [[ -n "${SEYMOUR_MININGCORE_DATABASE_URL:-}" ]]; then
  if psql "$SEYMOUR_MININGCORE_DATABASE_URL" -v ON_ERROR_STOP=1 -Atqc 'SELECT 1' >/dev/null; then
    pass "MiningCore database connection"
  else
    fail "MiningCore database connection"
  fi
else
  warn "MiningCore DB not configured"
fi

printf '\nPackage 003 doctor passed.\n'
