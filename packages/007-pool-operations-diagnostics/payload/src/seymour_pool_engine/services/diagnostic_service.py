from typing import Any

from seymour_pool_engine.database import test_engine_database, test_miningcore_database
from seymour_pool_engine.repositories.diagnostic_repository import DiagnosticRepository

repository = DiagnosticRepository()


def _normalize_check(component: str, result: dict[str, Any]) -> dict[str, Any]:
    status_map = {
        "online": "passed",
        "offline": "failed",
        "disabled": "disabled",
    }
    return {
        "component": component,
        "status": status_map.get(result.get("status"), "warning"),
        "summary": result.get("summary", "No summary available"),
        "details": result.get("details", {}),
    }


def _readiness_score(checks: list[dict[str, Any]]) -> int:
    enabled = [check for check in checks if check["status"] != "disabled"]
    if not enabled:
        return 0
    weights = {"passed": 100, "warning": 50, "failed": 0}
    return round(sum(weights[check["status"]] for check in enabled) / len(enabled))


def run_pool_diagnostics(
    *,
    pool_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    checks = [
        _normalize_check("engine-database", test_engine_database()),
        _normalize_check("miningcore-database", test_miningcore_database()),
    ]
    score = _readiness_score(checks)
    if any(check["status"] == "failed" for check in checks):
        status = "failed"
    elif any(check["status"] in {"warning", "disabled"} for check in checks):
        status = "degraded"
    else:
        status = "passed"
    summary = f"Pool readiness score is {score}%"
    run_id = None
    if persist:
        run_id = repository.save_run(
            pool_id=pool_id,
            operation="pool.readiness",
            status=status,
            readiness_score=score,
            summary=summary,
            checks=checks,
        )
    return {
        "diagnosticRunId": str(run_id) if run_id else None,
        "poolId": pool_id,
        "operation": "pool.readiness",
        "status": status,
        "readinessScore": score,
        "summary": summary,
        "checks": checks,
    }


def get_diagnostic_runs(*, pool_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")
    runs = repository.list_runs(pool_id=pool_id, limit=limit)
    return {"count": len(runs), "runs": runs}
