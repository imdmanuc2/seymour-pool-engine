#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Doctor Package 026"; require_repo; pass "Repository root"
command -v rsync >/dev/null || fail "rsync available"; pass "rsync available"
command -v systemctl >/dev/null || fail "systemd available"; pass "systemd available"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/main.py" ]] || fail "API runtime"; pass "API runtime"
[[ -f "$REPO_ROOT/src/seymour_pool_engine/stratum_runtime.py" ]] || fail "Stratum runtime"; pass "Stratum runtime"
[[ -f "$REPO_ROOT/migrations/026_ckpool_competitive_acceptance_testing.sql" ]] || fail "Package 025 baseline"; pass "Package 025 baseline"
echo "Package 026 doctor PASS"
