#!/usr/bin/env bash
set -euo pipefail
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PAYLOAD_DIR="$PACKAGE_DIR/payload"; REPO_ROOT="$(cd "$PACKAGE_DIR/../.." && pwd)"; BACKUP_MARKER="$PACKAGE_DIR/.last_backup_dir"
heading(){ printf '\n== %s ==\n' "$1"; }; pass(){ printf '%-48s PASS\n' "$1"; }; fail(){ printf '%-48s FAIL\n' "$1" >&2; exit 1; }
require_repo(){ [[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "Repository root"; }; python_bin(){ [[ -x "$REPO_ROOT/.venv/bin/python" ]] && echo "$REPO_ROOT/.venv/bin/python" || command -v python3; }
