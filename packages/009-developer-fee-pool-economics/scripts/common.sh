#!/usr/bin/env bash
set -euo pipefail
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$PACKAGE_DIR/../.." && pwd)"
PAYLOAD_DIR="$PACKAGE_DIR/payload"
MIGRATION_ID="010_developer_fee_pool_economics"
MIGRATION_FILE="$PAYLOAD_DIR/migrations/010_developer_fee_pool_economics.sql"
BACKUP_MARKER="$PACKAGE_DIR/.last_backup_dir"
heading(){ printf '
== %s ==
' "$1"; }
pass(){ printf '%-47s PASS
' "$1"; }
fail(){ printf '%-47s FAIL
' "$1" >&2; exit 1; }
require_repo(){ [[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "Repository detected"; }
load_env(){ [[ -f "$REPO_ROOT/.env" ]] && set -a && source "$REPO_ROOT/.env" && set +a || true; }
python_bin(){ [[ -x "$REPO_ROOT/.venv/bin/python" ]] && printf '%s' "$REPO_ROOT/.venv/bin/python" || command -v python3; }
