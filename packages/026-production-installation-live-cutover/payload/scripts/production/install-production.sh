#!/usr/bin/env bash
set -euo pipefail
[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
SOURCE_ROOT="${SEYMOUR_SOURCE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; INSTALL_ROOT="${SEYMOUR_INSTALL_ROOT:-/opt/seymour-pool-engine}"
CONFIG_DIR=/etc/seymour-pool-engine; STATE_DIR=/var/lib/seymour-pool-engine; LOG_DIR=/var/log/seymour-pool-engine
id seymour-engine >/dev/null 2>&1 || useradd --system --home "$STATE_DIR" --shell /usr/sbin/nologin seymour-engine
install -d -o seymour-engine -g seymour-engine "$INSTALL_ROOT" "$STATE_DIR" "$LOG_DIR"; install -d -m 0750 -o root -g seymour-engine "$CONFIG_DIR"
rsync -a --delete --exclude .git --exclude .venv --exclude packages/backups "$SOURCE_ROOT/" "$INSTALL_ROOT/"
python3 -m venv "$INSTALL_ROOT/.venv"; "$INSTALL_ROOT/.venv/bin/python" -m pip install --upgrade pip; "$INSTALL_ROOT/.venv/bin/python" -m pip install "$INSTALL_ROOT"
if [[ ! -f "$CONFIG_DIR/engine.env" ]]; then install -m 0640 -o root -g seymour-engine "$SOURCE_ROOT/.env.production.example" "$CONFIG_DIR/engine.env"; fi
install -m 0644 "$SOURCE_ROOT/packaging/systemd/seymour-pool-engine-api.service" /etc/systemd/system/
install -m 0644 "$SOURCE_ROOT/packaging/systemd/seymour-pool-engine-stratum.service" /etc/systemd/system/
install -m 0644 "$SOURCE_ROOT/packaging/logrotate/seymour-pool-engine" /etc/logrotate.d/seymour-pool-engine
chown -R seymour-engine:seymour-engine "$INSTALL_ROOT" "$STATE_DIR" "$LOG_DIR"; systemctl daemon-reload
echo "Installation staged. CKPool was not modified. Edit /etc/seymour-pool-engine/engine.env before enabling services."
