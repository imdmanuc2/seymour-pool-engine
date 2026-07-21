#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 016"; require_repo; load_env
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file missing"; pass "Package files"
heading "Static checks"; PYTHON="$(python_bin)"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"; pass "Ruff"
heading "Test suite"; "$PYTHON" -m pytest -q "$REPO_ROOT/tests"; pass "Pytest"
heading "Database objects"
for check in \
  "Migration 017 recorded|SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='017_security_access_control'" \
  "security principals table|SELECT to_regclass('seymour_engine.security_principals') IS NOT NULL" \
  "security roles table|SELECT to_regclass('seymour_engine.security_roles') IS NOT NULL" \
  "security permissions table|SELECT to_regclass('seymour_engine.security_permissions') IS NOT NULL" \
  "principal roles table|SELECT to_regclass('seymour_engine.security_principal_roles') IS NOT NULL" \
  "API keys table|SELECT to_regclass('seymour_engine.security_api_keys') IS NOT NULL" \
  "sessions table|SELECT to_regclass('seymour_engine.security_sessions') IS NOT NULL" \
  "security events table|SELECT to_regclass('seymour_engine.security_events') IS NOT NULL" \
  "rate limit policies table|SELECT to_regclass('seymour_engine.security_rate_limit_policies') IS NOT NULL" \
  "approval requests table|SELECT to_regclass('seymour_engine.security_approval_requests') IS NOT NULL" \
  "system roles seeded|SELECT COUNT(*) >= 4 FROM seymour_engine.security_roles WHERE system_role"
do
  label="${check%%|*}"; sql="${check#*|}"; result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"
  [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"; pass "$label"
done
heading "Application import"
"$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'; pass "Application import"
heading "Security API routes"
"$PYTHON" - <<'PYTHON'
from seymour_pool_engine.main import app
paths=set(app.openapi()["paths"])
required={
 "/api/v1/security/principals", "/api/v1/security/roles",
 "/api/v1/security/principals/{principal_id}/roles",
 "/api/v1/security/principals/{principal_id}/permissions",
 "/api/v1/security/principals/{principal_id}/api-keys",
 "/api/v1/security/api-keys/{api_key_id}", "/api/v1/security/whoami",
 "/api/v1/security/authorize/{permission}", "/api/v1/security/events",
}
missing=required-paths
assert not missing, f"Missing security API routes: {sorted(missing)}"
PYTHON
pass "Security API routes"
printf '\nPackage 016 verified.\n'
