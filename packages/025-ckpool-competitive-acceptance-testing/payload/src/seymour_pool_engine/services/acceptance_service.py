from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from importlib import import_module
from typing import Any

from seymour_pool_engine.repositories.acceptance_repository import AcceptanceRepository


class AcceptanceService:
    REQUIRED_MODULES = (
        "seymour_pool_engine.stratum.dispatcher",
        "seymour_pool_engine.engines.jobs",
        "seymour_pool_engine.engines.blocks.builder",
        "seymour_pool_engine.services.block_submission_service",
        "seymour_pool_engine.services.node_failover_service",
        "seymour_pool_engine.services.vardiff_service",
    )
    REQUIRED_ROUTES = {
        "/api/v1/stratum/status",
        "/api/v1/templates/status",
        "/api/v1/block-candidates/status",
        "/api/v1/bitcoin/nodes/status",
    }

    def __init__(self, repository: AcceptanceRepository | None = None) -> None:
        self.repository = repository or AcceptanceRepository()

    def run(self, profile: str = "release", persist: bool = True) -> dict[str, Any]:
        started = time.perf_counter()
        checks: list[dict[str, Any]] = []
        self._check(checks, "runtime-modules", self._runtime_modules)
        self._check(checks, "api-contract", self._api_contract)
        self._check(checks, "sha256d-throughput", self._sha256d_throughput)
        passed = sum(1 for check in checks if check["passed"])
        report = {
            "profile": profile,
            "status": "passed" if passed == len(checks) else "failed",
            "checksTotal": len(checks),
            "checksPassed": passed,
            "durationMs": round((time.perf_counter() - started) * 1000, 3),
            "checks": checks,
        }
        if persist:
            report["runId"] = self.repository.record(profile, report)
        return report

    @staticmethod
    def _check(
        checks: list[dict[str, Any]],
        name: str,
        fn: Callable[[], dict[str, Any]],
    ) -> None:
        try:
            details = fn()
            checks.append({"name": name, "passed": True, "details": details})
        except Exception as exc:
            checks.append({"name": name, "passed": False, "error": str(exc)})

    def _runtime_modules(self) -> dict[str, Any]:
        for name in self.REQUIRED_MODULES:
            import_module(name)
        return {"modules": len(self.REQUIRED_MODULES)}

    def _api_contract(self) -> dict[str, Any]:
        from seymour_pool_engine.main import app

        paths = set(app.openapi()["paths"])
        missing = self.REQUIRED_ROUTES - paths
        if missing:
            raise RuntimeError(f"Missing API routes: {sorted(missing)}")
        return {
            "requiredRoutes": len(self.REQUIRED_ROUTES),
            "availableRoutes": len(paths),
        }

    @staticmethod
    def _sha256d_throughput() -> dict[str, Any]:
        payload = bytes(80)
        iterations = 10_000
        started = time.perf_counter()
        for _ in range(iterations):
            hashlib.sha256(hashlib.sha256(payload).digest()).digest()
        elapsed = max(time.perf_counter() - started, 1e-9)
        rate = iterations / elapsed
        if rate < 1_000:
            raise RuntimeError(f"SHA256d benchmark too slow: {rate:.0f}/s")
        return {"iterations": iterations, "hashesPerSecond": round(rate, 2)}
