#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
require_repo
[[ -f "$BACKUP_MARKER" ]] || fail "Backup marker"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"; [[ -d "$BACKUP_DIR" ]] || fail "Backup directory"
heading "Rollback Package 008"
if [[ -d "$BACKUP_DIR/.new-files" ]]; then while IFS= read -r -d '' marker; do relative="${marker#"$BACKUP_DIR/.new-files/"}"; rm -f "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR/.new-files" -type f -print0); fi
while IFS= read -r -d '' backup; do [[ "$backup" == "$BACKUP_DIR/.new-files/"* ]] && continue; relative="${backup#"$BACKUP_DIR/"}"; mkdir -p "$REPO_ROOT/$(dirname "$relative")"; cp -a "$backup" "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR" -type f -print0)
pass "Files restored"
printf '\nDatabase objects are retained to protect operational history.\nPackage 008 rollback complete.\n'
