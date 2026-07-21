#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 016"; require_repo; load_env
command -v psql >/dev/null || fail "psql command missing"; pass "psql command"
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc 'SELECT 1' >/dev/null; pass "Engine database connection"
PYTHON="$(python_bin)"; "$PYTHON" -c 'import fastapi, psycopg, pydantic' >/dev/null; pass "Python dependencies"
[[ -f "$REPO_ROOT/migrations/016_multi_coin_multi_wallet_operations.sql" ]] || fail "Package 015 baseline missing"; pass "Package 015 baseline"
printf '\nPackage 016 doctor passed.\n'
