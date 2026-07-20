#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Package 008 doctor"
require_repo; pass "Repository detected"
[[ -d "$PAYLOAD_DIR" ]] || fail "Package payload"; pass "Package payload"
PYTHON="$(python_bin)"; "$PYTHON" --version >/dev/null; pass "Python runtime"
[[ -f "$REPO_ROOT/.env" ]] || fail ".env configuration file"; pass ".env configuration file"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"; pass "Engine database URL"
command -v psql >/dev/null || fail "PostgreSQL client"; pass "PostgreSQL client"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc 'SELECT 1' >/dev/null || fail "Engine database connection"; pass "Engine database connection"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='008_pool_operations_diagnostics';")" == "1" ]] || fail "Package 007 diagnostics"; pass "Package 007 diagnostics"
printf '\nPackage 008 doctor passed.\n'
