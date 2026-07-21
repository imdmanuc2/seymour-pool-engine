#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 020"
require_repo; pass "Repository detected"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
pass "Engine database URL"
command -v psql >/dev/null || fail "PostgreSQL client"
pass "PostgreSQL client"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1" >/dev/null || fail "Database connection"
pass "Database connection"
[[ "$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='020_stratum_protocol_foundation';")" == "1" ]] || fail "Package 019 prerequisite"
pass "Package 019 prerequisite"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/stratum/dispatcher.py" ]] || fail "Stratum foundation"
pass "Stratum foundation"
[[ -f "$MIGRATION_FILE" ]] || fail "Package payload"
pass "Package payload"
