from __future__ import annotations

from typing import Any

import pytest

from seymour_pool_engine.providers.bitcoin.resilience import ResilientBitcoinRpcClient
from seymour_pool_engine.providers.bitcoin.rpc import BitcoinRpcError


class FakeClient:
    behavior: dict[str, list[Any]] = {}

    def __init__(self, url: str, *_args: Any) -> None:
        self.url = url

    def call(self, _method: str, _params: list[Any] | None = None) -> Any:
        value = self.behavior[self.url].pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def client(urls: list[str], *, threshold: int = 1, cooldown: float = 30.0, clock=lambda: 0.0):
    return ResilientBitcoinRpcClient(
        urls,
        failure_threshold=threshold,
        cooldown_seconds=cooldown,
        client_factory=FakeClient,
        clock=clock,
    )


def test_primary_endpoint_is_used_when_healthy() -> None:
    FakeClient.behavior = {"a": [{"chain": "main"}], "b": []}
    rpc = client(["a", "b"])
    assert rpc.get_blockchain_info()["chain"] == "main"
    assert rpc.url == "a"


def test_failover_selects_secondary_endpoint() -> None:
    FakeClient.behavior = {"a": [BitcoinRpcError("down")], "b": [{"chain": "main"}]}
    rpc = client(["a", "b"])
    assert rpc.get_blockchain_info()["chain"] == "main"
    assert rpc.url == "b"


def test_active_secondary_remains_preferred() -> None:
    FakeClient.behavior = {
        "a": [BitcoinRpcError("down")],
        "b": [{"chain": "main"}, {"blocks": 10}],
    }
    rpc = client(["a", "b"])
    rpc.get_blockchain_info()
    assert rpc.call("getblockcount") == {"blocks": 10}


def test_all_endpoint_failures_are_reported() -> None:
    FakeClient.behavior = {
        "a": [BitcoinRpcError("a down")],
        "b": [BitcoinRpcError("b down")],
    }
    rpc = client(["a", "b"])
    with pytest.raises(BitcoinRpcError, match="All Bitcoin RPC endpoints failed"):
        rpc.call("getblockcount")


def test_circuit_breaker_opens_after_threshold() -> None:
    FakeClient.behavior = {
        "a": [BitcoinRpcError("down")],
        "b": [{"chain": "main"}],
    }
    rpc = client(["a", "b"], threshold=1)
    rpc.get_blockchain_info()
    status = rpc.status()
    assert status["endpoints"][0]["available"] is False


def test_circuit_recovers_after_cooldown() -> None:
    now = [0.0]
    FakeClient.behavior = {
        "a": [BitcoinRpcError("down"), {"blocks": 20}],
        "b": [{"blocks": 10}, BitcoinRpcError("secondary down")],
    }
    rpc = client(["a", "b"], threshold=1, cooldown=5.0, clock=lambda: now[0])
    assert rpc.call("getblockcount") == {"blocks": 10}
    now[0] = 6.0
    assert rpc.call("getblockcount") == {"blocks": 20}
    assert rpc.url == "a"


def test_duplicate_urls_are_removed() -> None:
    FakeClient.behavior = {"a": [{"blocks": 1}]}
    rpc = client(["a", "a"])
    assert rpc.status()["endpointCount"] == 1


def test_empty_endpoint_list_is_rejected() -> None:
    with pytest.raises(ValueError, match="At least one"):
        client([])
