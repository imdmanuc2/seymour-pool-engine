#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"; heading "Install Package 026"; require_repo
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP_DIR="$REPO_ROOT/packages/backups/026-production-installation-live-cutover-$STAMP"; mkdir -p "$BACKUP_DIR"; echo "$BACKUP_DIR" > "$BACKUP_MARKER"
while IFS= read -r -d '' source_file; do relative="${source_file#"$PAYLOAD_DIR/"}"; target="$REPO_ROOT/$relative"; if [[ -f "$target" ]]; then mkdir -p "$BACKUP_DIR/$(dirname "$relative")"; cp -a "$target" "$BACKUP_DIR/$relative"; else mkdir -p "$BACKUP_DIR/.new-files/$(dirname "$relative")"; : > "$BACKUP_DIR/.new-files/$relative"; fi; done < <(find "$PAYLOAD_DIR" -type f -print0)
pass "File backup"; cp -a "$PAYLOAD_DIR/." "$REPO_ROOT/"; chmod +x "$REPO_ROOT"/scripts/production/*.sh; pass "Payload installed"
PYTHON="$(python_bin)"; "$PYTHON" -m pip install -e "$REPO_ROOT[dev]"; pass "Python project installed"; printf '\nPackage 026 installed.\nBackup: %s\n' "$BACKUP_DIR"
