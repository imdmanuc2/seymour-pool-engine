#!/usr/bin/env bash
set -euo pipefail
[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
/opt/seymour-pool-engine/scripts/production/preflight.sh
systemctl enable --now seymour-pool-engine-api.service seymour-pool-engine-stratum.service
sleep 2; /opt/seymour-pool-engine/scripts/production/health-check.sh
