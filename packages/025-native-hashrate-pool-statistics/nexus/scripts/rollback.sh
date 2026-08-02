#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
require_repo
[[ -f "$BACKUP_MARKER" ]] || fail "No backup marker found"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"
[[ -d "$BACKUP_DIR" ]] || fail "Backup directory not found: $BACKUP_DIR"
heading "Rollback Package 025"
if [[ -d "$BACKUP_DIR/.new-files" ]]; then
  while IFS= read -r -d '' marker; do
    relative="${marker#"$BACKUP_DIR/.new-files/"}"
    rm -f "$REPO_ROOT/$relative"
  done < <(find "$BACKUP_DIR/.new-files" -type f -print0)
fi
while IFS= read -r -d '' backup_file; do
  [[ "$backup_file" == "$BACKUP_DIR/.new-files/"* ]] && continue
  relative="${backup_file#"$BACKUP_DIR/"}"
  mkdir -p "$REPO_ROOT/$(dirname "$relative")"
  cp -a "$backup_file" "$REPO_ROOT/$relative"
done < <(find "$BACKUP_DIR" -type f -print0)
pass "Files restored"
printf '\nDatabase migration 026 is additive and is not removed automatically.\n'
