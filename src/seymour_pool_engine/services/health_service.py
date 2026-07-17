from datetime import UTC, datetime

from seymour_pool_engine.database import (
    test_engine_database,
    test_miningcore_database,
)


def _overall_status(checks: list[dict]) -> str:
    statuses = {check["status"] for check in checks}

    if "offline" in statuses:
        return "degraded"

    if statuses == {"disabled"}:
        return "unknown"

    return "online"


def get_health() -> dict:
    checks = [
        {
            "component": "engine-api",
            "status": "online",
            "summary": "Seymour Pool Engine API is responding",
            "details": {},
        },
        {
            "component": "engine-database",
            **test_engine_database(),
        },
        {
            "component": "miningcore-database",
            **test_miningcore_database(),
        },
    ]

    return {
        "status": _overall_status(checks),
        "observedAt": datetime.now(UTC).isoformat(),
        "checks": checks,
    }
