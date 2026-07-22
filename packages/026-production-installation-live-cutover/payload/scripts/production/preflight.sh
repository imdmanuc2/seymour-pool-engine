#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; ENV_FILE="${SEYMOUR_ENV_FILE:-/etc/seymour-pool-engine/engine.env}"
pass(){ printf '%-48s PASS\n' "$1"; }; fail(){ printf '%-48s FAIL\n' "$1" >&2; exit 1; }
command -v python3 >/dev/null || fail "python3 installed"; pass "python3 installed"
command -v psql >/dev/null || fail "PostgreSQL client installed"; pass "PostgreSQL client installed"
[[ -f "$ROOT/pyproject.toml" ]] || fail "Repository root"; pass "Repository root"
[[ -f "$ENV_FILE" ]] || fail "Production environment file"; pass "Production environment file"
set -a; source "$ENV_FILE"; set +a
[[ "${SEYMOUR_ENGINE_DATABASE_URL:-}" == postgresql://* ]] || fail "Database URL configured"; pass "Database URL configured"
[[ -n "${SEYMOUR_BITCOIN_RPC_USER:-}" && "${SEYMOUR_BITCOIN_RPC_USER}" != CHANGE_ME ]] || fail "Bitcoin RPC user configured"; pass "Bitcoin RPC user configured"
[[ -n "${SEYMOUR_BITCOIN_RPC_PASSWORD:-}" && "${SEYMOUR_BITCOIN_RPC_PASSWORD}" != CHANGE_ME ]] || fail "Bitcoin RPC password configured"; pass "Bitcoin RPC password configured"
[[ -n "${SEYMOUR_BITCOIN_PAYOUT_SCRIPT:-}" && "${SEYMOUR_BITCOIN_PAYOUT_SCRIPT}" != CHANGE_ME && "${SEYMOUR_BITCOIN_PAYOUT_SCRIPT}" != 51 ]] || fail "Safe payout script configured"; pass "Safe payout script configured"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -Atqc 'select 1' | grep -qx 1 || fail "Database connectivity"; pass "Database connectivity"
printf '\nPreflight passed. No services or miners were changed.\n'
