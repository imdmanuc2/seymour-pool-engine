#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 017"; require_repo; pass "Repository detected"; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
command -v psql >/dev/null || fail "psql available"; pass "psql available"
command -v pg_dump >/dev/null || fail "pg_dump available"; pass "pg_dump available"
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file present"; pass "Migration file present"
PYTHON="$(python_bin)"; "$PYTHON" -c 'import fastapi, psycopg' >/dev/null; pass "Python dependencies"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc 'SELECT 1' | grep -qx 1 || fail "Database connectivity"; pass "Database connectivity"
printf '\nPackage 017 doctor checks passed.\n'
