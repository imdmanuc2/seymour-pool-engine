#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

heading "Package 002 doctor"
require_repo
pass "Repository detected"

[[ -d "$PAYLOAD_DIR" ]] || fail "Package payload"
[[ -f "$PAYLOAD_DIR/migrations/003_worker_lifecycle.sql" ]] || fail "Worker migration"
pass "Package payload"

PYTHON="$(python_bin)"
"$PYTHON" --version >/dev/null
pass "Python runtime"

[[ -f "$REPO_ROOT/.env" ]] || fail ".env configuration file"
pass ".env configuration file"

load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
[[ -n "${SEYMOUR_MININGCORE_DATABASE_URL:-}" ]] || fail "SEYMOUR_MININGCORE_DATABASE_URL"
pass "Database URLs configured"

command -v psql >/dev/null 2>&1 || fail "PostgreSQL client"
pass "PostgreSQL client"

psql "$SEYMOUR_ENGINE_DATABASE_URL" -v ON_ERROR_STOP=1 -Atqc 'SELECT 1' >/dev/null \
  || fail "Engine database connection"
pass "Engine database connection"

psql "$SEYMOUR_MININGCORE_DATABASE_URL" -v ON_ERROR_STOP=1 -Atqc 'SELECT 1' >/dev/null \
  || fail "MiningCore database connection"
pass "MiningCore database connection"

[[ -f "$REPO_ROOT/src/seymour_pool_engine/providers/base.py" ]] \
  || fail "Package 001B provider foundation"
pass "Package 001B provider foundation"

printf '\nPackage 002 doctor passed.\n'
