#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 013"
require_repo; pass "Repository detected"
[[ -f "$MIGRATION_FILE" ]] || fail "Package files"; pass "Package files"
command -v psql >/dev/null || fail "psql available"; pass "psql available"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1" >/dev/null; pass "Database connection"
python_bin >/dev/null; pass "Python available"
printf '\nPackage 013 doctor checks passed.\n'
