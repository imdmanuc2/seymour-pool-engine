#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Install Package 019"
require_repo; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "Engine database URL"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$REPO_ROOT/packages/backups/019-native-stratum-protocol-foundation-$STAMP"
mkdir -p "$BACKUP_DIR"
printf '%s\n' "$BACKUP_DIR" > "$BACKUP_MARKER"
heading "Backup replaced files"
while IFS= read -r -d '' source_file; do
  relative="${source_file#"$PAYLOAD_DIR/"}"
  target="$REPO_ROOT/$relative"
  if [[ -f "$target" ]]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$relative")"
    cp -a "$target" "$BACKUP_DIR/$relative"
  else
    mkdir -p "$BACKUP_DIR/.new-files/$(dirname "$relative")"
    : > "$BACKUP_DIR/.new-files/$relative"
  fi
done < <(find "$PAYLOAD_DIR" -type f -print0)
pass "File backup"
heading "Install package payload"
cp -a "$PAYLOAD_DIR/." "$REPO_ROOT/"
pass "Payload installed"
heading "Install Python project"
PYTHON="$(python_bin)"
"$PYTHON" -m pip install -e "$REPO_ROOT[dev]"
pass "Python project installed"
heading "Apply database migration"
psql "$SEYMOUR_ENGINE_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$REPO_ROOT/migrations/020_stratum_protocol_foundation.sql"
pass "Migration 020"
printf '\nPackage 019 installed.\nBackup: %s\n' "$BACKUP_DIR"
