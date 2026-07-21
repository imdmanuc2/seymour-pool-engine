#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 022"; require_repo; load_env; PYTHON="$(python_bin)"; cd "$REPO_ROOT"
heading "Static checks"; "$PYTHON" -m ruff check src tests; pass "Ruff"
heading "Block construction tests"; "$PYTHON" -m pytest -q tests/test_block_construction_submitblock.py tests/test_share_validation_pipeline.py; pass "Block construction tests"
heading "Database objects"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT EXISTS(SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='023_block_construction_submitblock')" | grep -qx t || fail "Migration 023 recorded"; pass "Migration 023 recorded"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "SELECT to_regclass('seymour_engine.bitcoin_block_candidates') IS NOT NULL" | grep -qx t || fail "bitcoin block candidates table"; pass "bitcoin block candidates table"
heading "Application routes"
"$PYTHON" - <<'PYROUTES'
from seymour_pool_engine.main import app

paths = set(app.openapi()["paths"])
required = {
    "/api/v1/block-candidates",
    "/api/v1/block-candidates/status",
}
missing = required - paths
assert not missing, f"Missing routes: {sorted(missing)}"
PYROUTES
pass "Block candidate API routes"

heading "Runtime imports"; "$PYTHON" - <<'PY'
from seymour_pool_engine.engines.blocks.builder import assemble_block
from seymour_pool_engine.services.block_submission_service import BlockSubmissionService
assert assemble_block and BlockSubmissionService
PY
pass "Block submission imports"
printf '
Package 022 verified.
'
