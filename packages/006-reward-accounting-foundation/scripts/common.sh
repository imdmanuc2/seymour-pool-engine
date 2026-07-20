#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PACKAGE_DIR/../.." && pwd)"
PAYLOAD_DIR="$PACKAGE_DIR/payload"
MIGRATION_ID="007_reward_accounting_foundation"
MIGRATION_FILE="$REPO_ROOT/migrations/007_reward_accounting_foundation.sql"
BACKUP_MARKER="$PACKAGE_DIR/.last_backup_dir"
heading() { printf '\n== %s ==\n' "$1"; }
pass() { printf '%-45s PASS\n' "$1"; }
fail() { printf '%-45s FAIL\n' "$1" >&2; exit 1; }
python_bin() { if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then printf '%s\n' "$REPO_ROOT/.venv/bin/python"; elif command -v python3 >/dev/null; then command -v python3; else fail "Python runtime"; fi; }
load_env() { if [[ -f "$REPO_ROOT/.env" ]]; then set -a; source "$REPO_ROOT/.env"; set +a; fi; }
require_repo() { [[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "Seymour Pool Engine repository"; grep -q 'name = "seymour-pool-engine"' "$REPO_ROOT/pyproject.toml" || fail "Seymour Pool Engine repository"; }
