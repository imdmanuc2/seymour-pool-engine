#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

heading "Package 001B doctor"
require_repo
pass "Repository detected"

[[ -d "$PAYLOAD_DIR" ]] || fail "Package payload"
[[ -f "$PAYLOAD_DIR/package-does-not-exist" ]] && fail "Package payload"
pass "Package payload"

PYTHON="$(python_bin)"
"$PYTHON" --version >/dev/null
pass "Python runtime"

[[ -f "$REPO_ROOT/.env" ]] || fail ".env configuration file"
pass ".env configuration file"

load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
pass "Engine database URL configured"

command -v psql >/dev/null 2>&1 || fail "PostgreSQL client"
pass "PostgreSQL client"

psql "$SEYMOUR_ENGINE_DATABASE_URL" -v ON_ERROR_STOP=1 -Atqc 'SELECT 1' >/dev/null \
  || fail "Engine database connection"
pass "Engine database connection"

[[ -f "$REPO_ROOT/migrations/001_engine_foundation.sql" ]] \
  || fail "Package 001A foundation"
pass "Package 001A foundation"

printf '\nPackage 001B doctor passed.\n'
