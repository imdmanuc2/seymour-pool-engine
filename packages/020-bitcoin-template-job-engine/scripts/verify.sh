#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 020"
require_repo; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
PYTHON="$(python_bin)"
heading "Static checks"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"
pass "Ruff"
heading "Bitcoin template and job tests"
"$PYTHON" -m pytest -q \
  "$REPO_ROOT/tests/test_bitcoin_template_job_engine.py" \
  "$REPO_ROOT/tests/test_bitcoin_rpc_provider.py" \
  "$REPO_ROOT/tests/test_stratum_dispatcher.py" \
  "$REPO_ROOT/tests/test_stratum_server.py"
pass "Template and job tests"
heading "Database objects"
for check in \
  "Migration 021 recorded|SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='021_bitcoin_template_job_engine'" \
  "block templates table|SELECT to_regclass('seymour_engine.bitcoin_block_templates') IS NOT NULL" \
  "job template height column|SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='seymour_engine' AND table_name='stratum_jobs' AND column_name='template_height'"; do
  label="${check%%|*}"; sql="${check#*|}"
  result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"
  [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"
  pass "$label"
done
heading "Application routes"
"$PYTHON" -c 'from seymour_pool_engine.main import app; p=set(app.openapi()["paths"]); r={"/api/v1/templates/status","/api/v1/templates/refresh"}; assert not r-p, sorted(r-p)'
pass "Template API routes"
heading "Runtime imports"
"$PYTHON" -c 'from seymour_pool_engine.engines.jobs.bitcoin import create_stratum_job; from seymour_pool_engine.providers.bitcoin import BitcoinRpcClient; from seymour_pool_engine.services.template_job_service import TemplateJobService; assert create_stratum_job and BitcoinRpcClient and TemplateJobService'
pass "Template runtime imports"
printf '\nPackage 020 verified.\n'
