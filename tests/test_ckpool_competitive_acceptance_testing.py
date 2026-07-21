from unittest.mock import Mock

from fastapi.testclient import TestClient

from seymour_pool_engine.main import app
from seymour_pool_engine.services.acceptance_service import AcceptanceService


def test_release_acceptance_passes_without_persistence():
    report = AcceptanceService(repository=Mock()).run(persist=False)
    assert report["status"] == "passed"
    assert report["checksPassed"] == report["checksTotal"] == 3


def test_runtime_module_check():
    result = AcceptanceService(repository=Mock())._runtime_modules()
    assert result["modules"] >= 6


def test_api_contract_check():
    result = AcceptanceService(repository=Mock())._api_contract()
    assert result["requiredRoutes"] == 4


def test_hash_benchmark_check():
    result = AcceptanceService(repository=Mock())._sha256d_throughput()
    assert result["hashesPerSecond"] > 1000


def test_failed_check_is_captured():
    checks = []
    AcceptanceService._check(checks, "failure", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert checks == [{"name": "failure", "passed": False, "error": "boom"}]


def test_acceptance_routes_exist():
    paths = set(app.openapi()["paths"])
    assert "/api/v1/acceptance/run" in paths
    assert "/api/v1/acceptance/runs" in paths
    assert "/api/v1/acceptance/criteria" in paths


def test_acceptance_criteria_endpoint():
    response = TestClient(app).get("/api/v1/acceptance/criteria")
    assert response.status_code == 200
    assert "comparison" in response.json()


def test_persisted_report_receives_run_id():
    repository = Mock()
    repository.record.return_value = "run-1"
    report = AcceptanceService(repository=repository).run(persist=True)
    assert report["runId"] == "run-1"
    repository.record.assert_called_once()
