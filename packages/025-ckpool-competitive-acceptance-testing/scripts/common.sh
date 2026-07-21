#!/usr/bin/env bash
set -euo pipefail
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$PACKAGE_DIR/../.." && pwd)"
PAYLOAD_DIR="$PACKAGE_DIR/payload"
BACKUP_MARKER="$PACKAGE_DIR/.last_backup_dir"
heading(){ printf '\n== %s ==\n' "$1"; }
pass(){ printf '%-47s PASS\n' "$1"; }
fail(){ printf '%-47s FAIL\n' "$1" >&2; exit 1; }
require_repo(){ [[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "Repository detected"; }
load_env(){ [[ -f "$REPO_ROOT/.env" ]] && set -a && source "$REPO_ROOT/.env" && set +a || true; }
python_bin(){ [[ -x "$REPO_ROOT/.venv/bin/python" ]] && printf '%s' "$REPO_ROOT/.venv/bin/python" || command -v python3; }
