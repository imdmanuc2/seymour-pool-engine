#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Rollback Package 015"; require_repo
[[ -f "$BACKUP_MARKER" ]] || fail "Backup marker"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"; [[ -d "$BACKUP_DIR" ]] || fail "Backup directory"
while IFS= read -r -d '' marker; do
  relative="${marker#"$BACKUP_DIR/.new-files/"}"; rm -f "$REPO_ROOT/$relative"
done < <(find "$BACKUP_DIR/.new-files" -type f -print0 2>/dev/null || true)
while IFS= read -r -d '' backup; do
  relative="${backup#"$BACKUP_DIR/"}"; [[ "$relative" == .new-files/* ]] && continue
  mkdir -p "$REPO_ROOT/$(dirname "$relative")"; cp -a "$backup" "$REPO_ROOT/$relative"
done < <(find "$BACKUP_DIR" -type f -print0)
pass "Package files restored"
printf '\nPackage 015 files rolled back. Migration 016 is intentionally not dropped automatically.\n'
