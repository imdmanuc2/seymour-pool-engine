from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from seymour_pool_engine.services import health_monitoring_service


def test_collect_health_is_healthy_when_dependencies_are_online(monkeypatch):
    online = {"status": "online", "summary": "ok", "details": {}}
    monkeypatch.setattr(health_monitoring_service, "test_engine_database", lambda: online)
    monkeypatch.setattr(health_monitoring_service, "test_miningcore_database", lambda: online)

    result = health_monitoring_service.collect_health(persist=False)

    assert result["status"] == "healthy"
    assert result["alertsCreatedOrUpdated"] == 0


def test_collect_health_is_critical_when_dependency_is_offline(monkeypatch):
    online = {"status": "online", "summary": "ok", "details": {}}
    offline = {"status": "offline", "summary": "failed", "details": {}}
    monkeypatch.setattr(health_monitoring_service, "test_engine_database", lambda: offline)
    monkeypatch.setattr(health_monitoring_service, "test_miningcore_database", lambda: online)

    result = health_monitoring_service.collect_health(persist=False)

    assert result["status"] == "critical"


def test_invalid_alert_filter_is_rejected():
    with pytest.raises(ValueError, match="invalid alert status"):
        health_monitoring_service.list_alerts(status="unknown")


def test_suppression_requires_future_time(monkeypatch):
    past = datetime.now(UTC) - timedelta(minutes=1)
    with pytest.raises(ValueError, match="future"):
        health_monitoring_service.suppress_alert(
            alert_id=uuid4(),
            actor="operator",
            until=past,
            reason="maintenance",
        )
