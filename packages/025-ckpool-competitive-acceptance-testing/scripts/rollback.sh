#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Rollback Package 025"
require_repo
[[ -f "$BACKUP_MARKER" ]] || fail "Backup marker"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"
[[ -d "$BACKUP_DIR" ]] || fail "Backup directory"
if [[ -d "$BACKUP_DIR/.new-files" ]]; then
 while IFS= read -r -d '' marker; do relative="${marker#"$BACKUP_DIR/.new-files/"}"; rm -f "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR/.new-files" -type f -print0)
fi
while IFS= read -r -d '' backup; do
 relative="${backup#"$BACKUP_DIR/"}"; [[ "$relative" == .new-files/* ]] && continue
 mkdir -p "$REPO_ROOT/$(dirname "$relative")"; cp -a "$backup" "$REPO_ROOT/$relative"
done < <(find "$BACKUP_DIR" -type f -print0)
pass "Files restored"
printf '\nPackage 025 rollback complete. Database migration remains recorded for audit safety.\n'
