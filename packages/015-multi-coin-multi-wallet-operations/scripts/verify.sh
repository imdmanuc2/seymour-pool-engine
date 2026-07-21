#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Verify Package 015"; require_repo; load_env
[[ -f "$MIGRATION_FILE" ]] || fail "Migration file missing"; pass "Package files"
heading "Static checks"; PYTHON="$(python_bin)"
"$PYTHON" -m ruff check "$REPO_ROOT/src" "$REPO_ROOT/tests"; pass "Ruff"
heading "Test suite"; "$PYTHON" -m pytest -q "$REPO_ROOT/tests"; pass "Pytest"
heading "Database objects"
for check in \
  "Migration 016 recorded|SELECT 1 FROM seymour_engine.schema_migrations WHERE migration_id='016_multi_coin_multi_wallet_operations'" \
  "coin registry table|SELECT to_regclass('seymour_engine.coin_registry') IS NOT NULL" \
  "coin networks table|SELECT to_regclass('seymour_engine.coin_networks') IS NOT NULL" \
  "wallet assignments table|SELECT to_regclass('seymour_engine.wallet_assignments') IS NOT NULL" \
  "wallet selection policies table|SELECT to_regclass('seymour_engine.wallet_selection_policies') IS NOT NULL" \
  "wallet reserves table|SELECT to_regclass('seymour_engine.wallet_reserves') IS NOT NULL" \
  "wallet balances table|SELECT to_regclass('seymour_engine.wallet_balance_snapshots') IS NOT NULL" \
  "wallet health table|SELECT to_regclass('seymour_engine.wallet_health') IS NOT NULL" \
  "wallet reconciliation table|SELECT to_regclass('seymour_engine.wallet_reconciliation_events') IS NOT NULL" \
  "wallet selection index|SELECT COUNT(*) > 0 FROM pg_indexes WHERE schemaname='seymour_engine' AND indexname='idx_wallets_selection'"
do
  label="${check%%|*}"; sql="${check#*|}"; result="$(psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc "$sql")"
  [[ "$result" == "1" || "$result" == "t" ]] || fail "$label"; pass "$label"
done
heading "Application import"
"$PYTHON" -c 'from seymour_pool_engine.main import app; assert app'; pass "Application import"
heading "Multi-wallet API routes"
"$PYTHON" - <<'PYTHON'
from seymour_pool_engine.main import app
paths=set(app.openapi()["paths"])
required={
 "/api/v1/coins", "/api/v1/coin-networks", "/api/v1/wallet-operations/assignments",
 "/api/v1/wallet-operations/policies", "/api/v1/wallet-operations/select",
 "/api/v1/wallet-operations/wallets/{wallet_id}/reserve",
 "/api/v1/wallet-operations/wallets/{wallet_id}/balances",
 "/api/v1/wallet-operations/wallets/{wallet_id}/health",
 "/api/v1/wallet-operations/wallets/{wallet_id}/reconcile",
}
missing=required-paths
assert not missing, f"Missing multi-wallet API routes: {sorted(missing)}"
PYTHON
pass "Multi-wallet API routes"
printf '\nPackage 015 verified.\n'
