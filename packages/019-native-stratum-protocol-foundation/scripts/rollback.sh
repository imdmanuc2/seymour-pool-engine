#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Rollback Package 019"
require_repo
[[ -f "$BACKUP_MARKER" ]] || fail "No Package 019 backup marker found"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"
[[ -d "$BACKUP_DIR" ]] || fail "Backup directory missing"
while IFS= read -r -d '' marker; do
  relative="${marker#"$BACKUP_DIR/.new-files/"}"
  rm -f "$REPO_ROOT/$relative"
done < <(find "$BACKUP_DIR/.new-files" -type f -print0 2>/dev/null || true)
while IFS= read -r -d '' backup; do
  [[ "$backup" == "$BACKUP_DIR/.new-files/"* ]] && continue
  relative="${backup#"$BACKUP_DIR/"}"
  mkdir -p "$REPO_ROOT/$(dirname "$relative")"
  cp -a "$backup" "$REPO_ROOT/$relative"
done < <(find "$BACKUP_DIR" -type f -print0)
printf '\nPackage 019 files restored from %s\nDatabase objects are retained for audit safety.\n' "$BACKUP_DIR"
