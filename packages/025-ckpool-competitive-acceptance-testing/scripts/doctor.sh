#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 025"
require_repo; load_env
command -v psql >/dev/null || fail "psql available"
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
PYTHON="$(python_bin)"
"$PYTHON" -c 'import fastapi, psycopg, pytest' || fail "Python dependencies"
pass "Repository and dependencies"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1" | grep -qx 1 || fail "Database connection"
pass "Database connection"
printf '\nPackage 025 doctor passed.\n'
