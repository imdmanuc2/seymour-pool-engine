import os
import platform
import socket
import time
from datetime import UTC, datetime

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.identity import get_or_create_installation_id

_PROCESS_STARTED_AT = time.monotonic()
_PROCESS_STARTED_WALL_CLOCK = datetime.now(UTC)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_system_information() -> dict:
    settings = get_settings()
    uptime_seconds = max(0, int(time.monotonic() - _PROCESS_STARTED_AT))

    return {
        "product": settings.product_name,
        "displayName": settings.display_name,
        "version": settings.version,
        "apiVersion": settings.api_version,
        "environment": settings.environment,
        "installationId": get_or_create_installation_id(),
        "hostname": socket.gethostname(),
        "processId": os.getpid(),
        "startedAt": _PROCESS_STARTED_WALL_CLOCK.isoformat(),
        "observedAt": utc_now_iso(),
        "uptimeSeconds": uptime_seconds,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "pythonVersion": platform.python_version(),
        },
    }
