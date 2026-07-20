#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
heading "Install Package 004"
require_repo; load_env
[[ -n "${SEYMOUR_ENGINE_DATABASE_URL:-}" ]] || fail "SEYMOUR_ENGINE_DATABASE_URL"
command -v psql >/dev/null || fail "PostgreSQL client"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$REPO_ROOT/packages/backups/004-statistics-engine-$STAMP"
mkdir -p "$BACKUP_DIR"; printf '%s\n' "$BACKUP_DIR" > "$BACKUP_MARKER"
heading "Backup replaced files"
while IFS= read -r -d '' source_file; do relative="${source_file#"$PAYLOAD_DIR/"}"; target="$REPO_ROOT/$relative"; if [[ -f "$target" ]]; then mkdir -p "$BACKUP_DIR/$(dirname "$relative")"; cp -a "$target" "$BACKUP_DIR/$relative"; else mkdir -p "$BACKUP_DIR/.new-files/$(dirname "$relative")"; : > "$BACKUP_DIR/.new-files/$relative"; fi; done < <(find "$PAYLOAD_DIR" -type f -print0)
pass "File backup"
heading "Install package payload"; cp -a "$PAYLOAD_DIR/." "$REPO_ROOT/"; pass "Payload installed"
heading "Install Python project"; PYTHON="$(python_bin)"; "$PYTHON" -m pip install -e "$REPO_ROOT[dev]"; pass "Python project installed"
heading "Apply database migration"; psql "$SEYMOUR_ENGINE_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$MIGRATION_FILE"; pass "Migration 005"
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^seymour-pool-engine.service'; then heading "Restart service"; sudo systemctl restart seymour-pool-engine.service; pass "Service restarted"; fi
printf '\nPackage 004 installed.\nBackup: %s\n' "$BACKUP_DIR"
