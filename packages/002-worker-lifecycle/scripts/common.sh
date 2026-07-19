#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PACKAGE_DIR/../.." && pwd)"
PAYLOAD_DIR="$PACKAGE_DIR/payload"
PACKAGE_ID="002"
MIGRATION_ID="003_worker_lifecycle"
MIGRATION_FILE="$REPO_ROOT/migrations/003_worker_lifecycle.sql"
BACKUP_MARKER="$PACKAGE_DIR/.last_backup_dir"

heading() { printf '\n== %s ==\n' "$1"; }
pass() { printf '%-45s PASS\n' "$1"; }
fail() { printf '%-45s FAIL\n' "$1" >&2; exit 1; }

python_bin() {
  if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    printf '%s\n' "$REPO_ROOT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    command -v python3
  else
    fail "Python runtime"
  fi
}

load_env() {
  if [[ -f "$REPO_ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
    set +a
  fi
}

require_repo() {
  [[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "Seymour Pool Engine repository"
  grep -q 'name = "seymour-pool-engine"' "$REPO_ROOT/pyproject.toml" \
    || fail "Seymour Pool Engine repository"
}
