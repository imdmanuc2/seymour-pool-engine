#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 018"; require_repo; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
command -v psql >/dev/null || fail "psql available"
pass "Repository detected"; pass "Database configuration"; pass "psql available"
[[ -f "$MIGRATION_FILE" ]] || fail "Package payload"; pass "Package payload"
