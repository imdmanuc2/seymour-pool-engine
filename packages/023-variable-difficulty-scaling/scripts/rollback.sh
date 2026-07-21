#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
[[ -f "$BACKUP_MARKER" ]] || fail "Backup marker"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"
[[ -d "$BACKUP_DIR" ]] || fail "Backup directory"
heading "Rollback Package 023"
if [[ -d "$BACKUP_DIR/.new-files" ]]; then
 while IFS= read -r -d '' marker; do relative="${marker#"$BACKUP_DIR/.new-files/"}"; rm -f "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR/.new-files" -type f -print0)
fi
while IFS= read -r -d '' source_file; do
 relative="${source_file#"$BACKUP_DIR/"}"; [[ "$relative" == .new-files/* ]] && continue
 mkdir -p "$REPO_ROOT/$(dirname "$relative")"; cp -a "$source_file" "$REPO_ROOT/$relative"
done < <(find "$BACKUP_DIR" -type f -print0)
pass "Files restored"
printf '\nDatabase migration 024 is intentionally retained for safe forward compatibility.\nPackage 023 rollback complete.\n'
