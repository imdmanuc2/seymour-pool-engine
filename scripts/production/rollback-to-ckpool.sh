#!/usr/bin/env bash
set -euo pipefail
[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
systemctl disable --now seymour-pool-engine-stratum.service || true; systemctl stop seymour-pool-engine-api.service || true
echo "Seymour services stopped. Restore CKPool as miner primary. CKPool configuration was not changed by this script."
