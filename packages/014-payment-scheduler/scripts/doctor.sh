#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 014"
require_repo; pass "Repository detected"
[[ -f "$MIGRATION_FILE" ]] && [[ -f "$PAYLOAD_DIR/src/seymour_pool_engine/services/payment_scheduler_service.py" ]] || fail "Package files"
pass "Package files"
command -v psql >/dev/null || fail "psql available"; pass "psql available"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Database connection"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc 'SELECT 1' >/dev/null || fail "Database connection"; pass "Database connection"
PYTHON="$(python_bin)"; "$PYTHON" --version >/dev/null || fail "Python available"; pass "Python available"
printf '\nPackage 014 doctor checks passed.\n'
