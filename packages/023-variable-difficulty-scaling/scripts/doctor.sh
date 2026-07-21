#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 023"
require_repo; pass "Repository detected"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
pass "Engine database URL"
command -v psql >/dev/null || fail "psql available"; pass "psql available"
PYTHON="$(python_bin)"; "$PYTHON" -c 'import sys; assert sys.version_info >= (3,11)' || fail "Python 3.11+"; pass "Python 3.11+"
[[ -f "$REPO_ROOT/migrations/023_block_construction_submitblock.sql" ]] || fail "Package 022 baseline"
pass "Package 022 baseline"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT 1" | grep -qx 1 || fail "Database connection"
pass "Database connection"
printf '\nPackage 023 doctor PASS\n'
