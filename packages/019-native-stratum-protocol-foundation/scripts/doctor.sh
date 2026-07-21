#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 019"
require_repo; pass "Repository detected"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
pass "Engine database URL"
command -v psql >/dev/null || fail "PostgreSQL client"
pass "PostgreSQL client"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1" >/dev/null || fail "Database connection"
pass "Database connection"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='019_nexus_integration_release_readiness';")" == "1" ]] || fail "Package 018 prerequisite"
pass "Package 018 prerequisite"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/api/router.py" ]] || fail "API router location"
pass "API router location"
[[ -f "$MIGRATION_FILE" ]] || fail "Package payload"
pass "Package payload"
