#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 022"
require_repo; pass "Repository detected"
load_env
command -v psql >/dev/null || fail "PostgreSQL client"; pass "PostgreSQL client"
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"; pass "Engine database URL"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1" | grep -qx 1 || fail "Database connection"; pass "Database connection"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT EXISTS(SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='022_share_validation_pipeline')" | grep -qx t || fail "Package 021 prerequisite"; pass "Package 021 prerequisite"
