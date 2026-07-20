#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
[[ -f "$BACKUP_MARKER" ]] || fail "Backup marker"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"; [[ -d "$BACKUP_DIR" ]] || fail "Backup directory"
heading "Rollback Package 004"
if [[ -d "$BACKUP_DIR/.new-files" ]]; then while IFS= read -r -d '' marker; do relative="${marker#"$BACKUP_DIR/.new-files/"}"; rm -f "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR/.new-files" -type f -print0); fi
while IFS= read -r -d '' file; do [[ "$file" == "$BACKUP_DIR/.new-files/"* ]] && continue; relative="${file#"$BACKUP_DIR/"}"; mkdir -p "$REPO_ROOT/$(dirname "$relative")"; cp -a "$file" "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR" -type f -print0)
pass "Files restored"
printf 'Database schema changes are retained for safety.\nPackage 004 rollback completed.\n'
