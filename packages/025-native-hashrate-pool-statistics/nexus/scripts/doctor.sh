#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 025"
require_repo; pass "Repository detected"
load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
pass "Engine database URL"
command -v psql >/dev/null || fail "psql available"; pass "psql available"
PYTHON="$(python_bin)"; "$PYTHON" -c 'import sys; assert sys.version_info >= (3,11)' || fail "Python 3.11+"; pass "Python 3.11+"
[[ -f "$REPO_ROOT/migrations/024_variable_difficulty_scaling.sql" ]] || fail "VarDiff baseline"
pass "VarDiff baseline"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT to_regclass('seymour_engine.stratum_submissions') IS NOT NULL" | grep -qx t || fail "Stratum submissions table"
pass "Stratum submissions table"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT to_regclass('seymour_engine.stratum_difficulty_history') IS NOT NULL" | grep -qx t || fail "VarDiff history table"
pass "VarDiff history table"
printf '\nPackage 025 doctor PASS\n'
