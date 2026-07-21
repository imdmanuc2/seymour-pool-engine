from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from seymour_pool_engine.engines.session.models import StratumSession
from seymour_pool_engine.engines.vardiff import VarDiffConfig, VarDiffController
from seymour_pool_engine.main import app


def session(difficulty: float = 8.0) -> StratumSession:
    return StratumSession("127.0.0.1", 1000, "abcd", 4, difficulty)


def config(**overrides) -> VarDiffConfig:
    values = {
        "target_share_seconds": 15.0,
        "retarget_interval_seconds": 30.0,
        "minimum_samples": 3,
        "damping": 0.5,
        "variance_percent": 10.0,
    }
    values.update(overrides)
    return VarDiffConfig(**values)


def test_first_share_initializes_state() -> None:
    s = session()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    decision = VarDiffController(config()).observe(s, now)
    assert not decision.changed
    assert decision.reason == "first-share"
    assert s.accepted_shares == 1


def test_fast_shares_raise_difficulty() -> None:
    s = session()
    controller = VarDiffController(config())
    start = datetime(2026, 1, 1, tzinfo=UTC)
    controller.observe(s, start)
    controller.observe(s, start + timedelta(seconds=2))
    controller.observe(s, start + timedelta(seconds=4))
    decision = controller.observe(s, start + timedelta(seconds=31))
    assert decision.changed
    assert decision.new_difficulty > decision.old_difficulty


def test_slow_shares_lower_difficulty() -> None:
    s = session(16.0)
    controller = VarDiffController(config(retarget_interval_seconds=60.0))
    start = datetime(2026, 1, 1, tzinfo=UTC)
    controller.observe(s, start)
    controller.observe(s, start + timedelta(seconds=40))
    decision = controller.observe(s, start + timedelta(seconds=80))
    assert decision.changed
    assert decision.new_difficulty < decision.old_difficulty


def test_variance_band_does_not_retarget() -> None:
    s = session()
    controller = VarDiffController(config(retarget_interval_seconds=20.0, minimum_samples=3))
    start = datetime(2026, 1, 1, tzinfo=UTC)
    controller.observe(s, start)
    controller.observe(s, start + timedelta(seconds=15))
    decision = controller.observe(s, start + timedelta(seconds=30))
    assert not decision.changed
    assert decision.reason == "within-variance"


def test_retarget_is_bounded() -> None:
    s = session(100.0)
    controller = VarDiffController(config(retarget_interval_seconds=1.0, max_step_factor=4.0))
    start = datetime(2026, 1, 1, tzinfo=UTC)
    controller.observe(s, start)
    controller.observe(s, start + timedelta(milliseconds=10))
    controller.observe(s, start + timedelta(milliseconds=20))
    decision = controller.observe(s, start + timedelta(seconds=2))
    assert decision.new_difficulty <= 200.0


def test_difficulty_respects_minimum() -> None:
    s = session(1.0)
    controller = VarDiffController(config(retarget_interval_seconds=1.0, min_difficulty=1.0))
    start = datetime(2026, 1, 1, tzinfo=UTC)
    controller.observe(s, start)
    controller.observe(s, start + timedelta(seconds=100))
    controller.observe(s, start + timedelta(seconds=200))
    controller.observe(s, start + timedelta(seconds=300))
    assert s.difficulty >= 1.0


def test_vardiff_routes_are_registered() -> None:
    paths = set(app.openapi()["paths"])
    assert "/api/v1/vardiff/status" in paths
    assert "/api/v1/vardiff/history" in paths


def test_status_route_with_stub(monkeypatch) -> None:
    from seymour_pool_engine.api.routes import vardiff as route_module

    class StubService:
        def status(self):
            return {"enabled": True, "activeSessions": 2}

    monkeypatch.setattr(route_module, "VarDiffService", StubService)
    response = TestClient(app).get("/api/v1/vardiff/status")
    assert response.status_code == 200
    assert response.json()["activeSessions"] == 2
