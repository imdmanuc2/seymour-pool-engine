#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"; heading "Verify Package 026"; require_repo; PYTHON="$(python_bin)"
heading "Static checks"; "$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"; pass "Ruff"
heading "Production deployment tests"; "$PYTHON" -m pytest -q "$REPO_ROOT/tests/test_production_installation_live_cutover.py"; pass "Production deployment tests"
heading "Shell syntax"; for s in "$REPO_ROOT"/scripts/production/*.sh "$PACKAGE_DIR"/scripts/*.sh; do bash -n "$s"; done; pass "Production script syntax"
heading "Documentation"; for d in 00-START-HERE.md 01-PRODUCTION-INSTALL.md 03-BITCOIN-CORE.md 05-FIRST-MINER.md 06-CKPOOL-LIVE-CUTOVER.md 10-TROUBLESHOOTING.md; do [[ -s "$REPO_ROOT/docs/$d" ]] || fail "$d"; done; pass "Required production documentation"
heading "Safety controls"; grep -q 'SEYMOUR_STRATUM_PORT=3334' "$REPO_ROOT/.env.production.example" || fail "Parallel Stratum port"; ! grep -RqiE 'systemctl (stop|disable).*ckpool' "$REPO_ROOT/scripts/production" || fail "CKPool protection"; pass "Non-destructive CKPool cutover"
echo "Package 026 verified."
