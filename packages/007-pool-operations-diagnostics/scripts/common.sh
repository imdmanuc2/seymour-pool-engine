#!/usr/bin/env bash
set -euo pipefail
PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$PACKAGE_ROOT/../.." && pwd)"
PAYLOAD_DIR="$PACKAGE_ROOT/payload"
MIGRATION_ID="008_pool_operations_diagnostics"
MIGRATION_FILE="$PAYLOAD_DIR/migrations/008_pool_operations_diagnostics.sql"
BACKUP_MARKER="$PACKAGE_ROOT/.last_backup_dir"
heading(){ printf '\n== %s ==\n' "$1"; }
pass(){ printf '%-46s PASS\n' "$1"; }
warn(){ printf '%-46s WARN\n' "$1"; }
fail(){ printf '%-46s FAIL\n' "$1" >&2; exit 1; }
require_repo(){ [[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "Repository detected"; }
load_env(){ if [[ -f "$REPO_ROOT/.env" ]]; then set -a; source "$REPO_ROOT/.env"; set +a; fi; }
python_bin(){ if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then echo "$REPO_ROOT/.venv/bin/python"; else command -v python3; fi; }
