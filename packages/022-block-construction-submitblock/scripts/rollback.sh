#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
require_repo
[[ -f "$BACKUP_MARKER" ]] || fail "Backup marker"
BACKUP_DIR="$(cat "$BACKUP_MARKER")"; [[ -d "$BACKUP_DIR" ]] || fail "Backup directory"
while IFS= read -r -d '' marker; do rel="${marker#"$BACKUP_DIR/.new-files/"}"; rm -f "$REPO_ROOT/$rel"; done < <(find "$BACKUP_DIR/.new-files" -type f -print0 2>/dev/null || true)
while IFS= read -r -d '' saved; do rel="${saved#"$BACKUP_DIR/"}"; [[ "$rel" == .new-files/* ]] && continue; mkdir -p "$REPO_ROOT/$(dirname "$rel")"; cp -a "$saved" "$REPO_ROOT/$rel"; done < <(find "$BACKUP_DIR" -type f -print0)
printf 'Files restored from %s
' "$BACKUP_DIR"
