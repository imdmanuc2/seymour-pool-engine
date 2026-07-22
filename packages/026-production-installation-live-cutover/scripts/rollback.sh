#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"; [[ -f "$BACKUP_MARKER" ]] || fail "Backup marker"; BACKUP_DIR="$(cat "$BACKUP_MARKER")"; [[ -d "$BACKUP_DIR" ]] || fail "Backup directory"
while IFS= read -r -d '' marker; do relative="${marker#"$BACKUP_DIR/.new-files/"}"; rm -f "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR/.new-files" -type f -print0 2>/dev/null || true)
while IFS= read -r -d '' file; do relative="${file#"$BACKUP_DIR/"}"; [[ "$relative" == .new-files/* ]] && continue; mkdir -p "$REPO_ROOT/$(dirname "$relative")"; cp -a "$file" "$REPO_ROOT/$relative"; done < <(find "$BACKUP_DIR" -type f -print0)
echo "Package 026 repository payload rolled back."
