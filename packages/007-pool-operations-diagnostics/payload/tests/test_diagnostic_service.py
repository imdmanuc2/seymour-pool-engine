from seymour_pool_engine.services import diagnostic_service


def test_readiness_passes_when_dependencies_are_online(monkeypatch):
    online = {"status": "online", "summary": "ok", "details": {}}
    monkeypatch.setattr(diagnostic_service, "test_engine_database", lambda: online)
    monkeypatch.setattr(diagnostic_service, "test_miningcore_database", lambda: online)

    result = diagnostic_service.run_pool_diagnostics(persist=False)

    assert result["status"] == "passed"
    assert result["readinessScore"] == 100


def test_readiness_degrades_when_optional_dependency_is_disabled(monkeypatch):
    online = {"status": "online", "summary": "ok", "details": {}}
    disabled = {"status": "disabled", "summary": "not configured", "details": {}}
    monkeypatch.setattr(diagnostic_service, "test_engine_database", lambda: online)
    monkeypatch.setattr(diagnostic_service, "test_miningcore_database", lambda: disabled)

    result = diagnostic_service.run_pool_diagnostics(persist=False)

    assert result["status"] == "degraded"
    assert result["readinessScore"] == 100
