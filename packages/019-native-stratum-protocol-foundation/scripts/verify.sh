#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 019"
require_repo; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
PYTHON="$(python_bin)"
heading "Static checks"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"
pass "Ruff"
heading "Stratum tests"
"$PYTHON" -m pytest -q \
  "$REPO_ROOT/tests/test_stratum_protocol.py" \
  "$REPO_ROOT/tests/test_stratum_dispatcher.py" \
  "$REPO_ROOT/tests/test_stratum_server.py"
pass "Stratum tests"
heading "Database objects"
for check in \
  "Migration 020 recorded|SELECT COUNT(*) FROM seymour_engine.schema_migrations WHERE migration_id='020_stratum_protocol_foundation'" \
  "stratum sessions table|SELECT to_regclass('seymour_engine.stratum_sessions') IS NOT NULL" \
  "stratum messages table|SELECT to_regclass('seymour_engine.stratum_messages') IS NOT NULL" \
  "stratum jobs table|SELECT to_regclass('seymour_engine.stratum_jobs') IS NOT NULL" \
  "stratum submissions table|SELECT to_regclass('seymour_engine.stratum_submissions') IS NOT NULL"; do
  label="${check%%|*}"; sql="${check#*|}"
  result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"
  [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"
  pass "$label"
done
heading "Application import"
"$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'
pass "Application import"
heading "Stratum API routes"
"$PYTHON" -c 'from seymour_pool_engine.main import app; p=set(app.openapi()["paths"]); r={"/api/v1/stratum/status","/api/v1/stratum/sessions"}; assert not r-p, sorted(r-p)'
pass "Stratum API routes"
heading "Runtime import"
"$PYTHON" -c 'from seymour_pool_engine.stratum.server import StratumServer; from seymour_pool_engine.stratum_runtime import main; assert StratumServer and main'
pass "Runtime import"
printf '\nPackage 019 verified.\n'
