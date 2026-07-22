#!/usr/bin/env bash
set -euo pipefail
ENV_FILE="${SEYMOUR_ENV_FILE:-/etc/seymour-pool-engine/engine.env}"; set -a; source "$ENV_FILE"; set +a
curl -fsS "http://127.0.0.1:${SEYMOUR_BIND_PORT:-8561}/api/${SEYMOUR_API_VERSION:-v1}/health" >/dev/null
printf '%-48s PASS\n' "Seymour API health"
timeout 3 bash -c "</dev/tcp/127.0.0.1/${SEYMOUR_STRATUM_PORT:-3334}" 2>/dev/null
printf '%-48s PASS\n' "Seymour Stratum listener"
systemctl is-active --quiet seymour-pool-engine-api.service; printf '%-48s PASS\n' "API systemd service"
systemctl is-active --quiet seymour-pool-engine-stratum.service; printf '%-48s PASS\n' "Stratum systemd service"
