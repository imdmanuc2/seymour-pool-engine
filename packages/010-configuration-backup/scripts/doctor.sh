#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 010"; require_repo; pass "Repository detected"
load_env
[[ -d "$PAYLOAD_DIR" ]] || fail "Package payload"
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file"
pass "Package files"
command -v psql >/dev/null || fail "psql available"; pass "psql available"
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc 'SELECT 1' | grep -qx 1 || fail "Database connection"
pass "Database connection"
PYTHON="$(python_bin)"; "$PYTHON" --version >/dev/null; pass "Python available"
printf '\nPackage 010 doctor checks passed.\n'
