#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 021"
require_repo; pass "Repository detected"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
command -v psql >/dev/null || fail "PostgreSQL client"
pass "PostgreSQL client"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1" >/dev/null || fail "Database connection"
pass "Database connection"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT EXISTS(SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='021_bitcoin_template_job_engine')" | grep -qx t || fail "Package 020 prerequisite"
pass "Package 020 prerequisite"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/stratum/dispatcher.py" ]] || fail "Stratum dispatcher"
pass "Stratum dispatcher"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/engines/jobs/models.py" ]] || fail "Bitcoin job models"
pass "Bitcoin job models"
