#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Package 005 doctor"
require_repo; pass "Repository detected"
[[ -d "$PAYLOAD_DIR" ]] || fail "Package payload"; pass "Package payload"
python_bin >/dev/null; pass "Python runtime"
[[ -f "$REPO_ROOT/.env" ]] || fail ".env configuration file"; pass ".env configuration file"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"; pass "Engine database URL"
command -v psql >/dev/null || fail "PostgreSQL client"; pass "PostgreSQL client"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc 'SELECT 1' >/dev/null || fail "Engine database connection"; pass "Engine database connection"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='005_statistics_engine';")" == "1" ]] || fail "Package 004 statistics engine"; pass "Package 004 statistics engine"
printf '\nPackage 005 doctor passed.\n'
