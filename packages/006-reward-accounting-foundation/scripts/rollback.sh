#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Rollback Package 006"
[[ -f "$BACKUP_MARKER" ]] || fail "Backup marker"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"
[[ -d "$BACKUP_DIR" ]] || fail "Backup directory"
if [[ -d "$BACKUP_DIR/.new-files" ]]; then while IFS= read -r -d '' marker; do relative="${marker#"$BACKUP_DIR/.new-files/"}"; rm -f "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR/.new-files" -type f -print0); fi
while IFS= read -r -d '' backup; do [[ "$backup" == "$BACKUP_DIR/.new-files/"* ]] && continue; relative="${backup#"$BACKUP_DIR/"}"; mkdir -p "$REPO_ROOT/$(dirname "$relative")"; cp -a "$backup" "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR" -type f -print0)
pass "Files restored"
printf '\nDatabase objects are preserved to avoid destructive rollback.\nPackage 006 file rollback completed.\n'
