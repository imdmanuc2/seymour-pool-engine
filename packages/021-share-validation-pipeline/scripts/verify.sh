#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 021"
require_repo; load_env
PYTHON="$(python_bin)"
heading "Static checks"
cd "$REPO_ROOT"
"$PYTHON" -m ruff check src tests
pass "Ruff"
heading "Share validation tests"
"$PYTHON" -m pytest -q tests/test_share_validation_pipeline.py tests/test_stratum_dispatcher.py
pass "Share validation tests"
heading "Database objects"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT EXISTS(SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='022_share_validation_pipeline')" | grep -qx t || fail "Migration 022 recorded"
pass "Migration 022 recorded"
for column in submission_fingerprint share_hash share_difficulty block_candidate header_hex; do
  psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='seymour_engine' AND table_name='stratum_submissions' AND column_name='$column')" | grep -qx t || fail "stratum_submissions.$column"
  pass "stratum_submissions.$column"
done
heading "Runtime imports"
"$PYTHON" - <<'PY'
from seymour_pool_engine.engines.shares.validator import validate_share
from seymour_pool_engine.stratum.dispatcher import StratumDispatcher
assert validate_share and StratumDispatcher
PY
pass "Share validator imports"
printf '\nPackage 021 verified.\n'
