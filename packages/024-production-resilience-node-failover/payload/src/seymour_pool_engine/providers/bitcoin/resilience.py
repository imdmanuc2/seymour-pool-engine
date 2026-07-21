from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import Any

from seymour_pool_engine.providers.bitcoin.rpc import BitcoinRpcClient, BitcoinRpcError


@dataclass(slots=True)
class EndpointState:
    url: str
    failures: int = 0
    successes: int = 0
    circuit_open_until: float = 0.0
    last_error: str | None = None
    last_success_at: float | None = None
    last_failure_at: float | None = None

    def available(self, now: float) -> bool:
        return self.circuit_open_until <= now


class ResilientBitcoinRpcClient:
    """Synchronous Bitcoin RPC client with ordered failover and circuit breaking."""

    def __init__(
        self,
        urls: list[str],
        username: str | None = None,
        password: str | None = None,
        timeout_seconds: float = 10.0,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30.0,
        client_factory: Callable[..., BitcoinRpcClient] = BitcoinRpcClient,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        cleaned = [url.strip() for url in urls if url.strip()]
        if not cleaned:
            raise ValueError("At least one Bitcoin RPC endpoint is required")
        self._states = [EndpointState(url) for url in dict.fromkeys(cleaned)]
        self._clients = {
            state.url: client_factory(state.url, username, password, timeout_seconds)
            for state in self._states
        }
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self._clock = clock
        self._active_index = 0
        self._lock = RLock()

    @property
    def url(self) -> str:
        return self._states[self._active_index].url

    def _ordered_indexes(self, now: float) -> list[int]:
        indexes = list(range(len(self._states)))
        indexes = indexes[self._active_index :] + indexes[: self._active_index]
        available = [i for i in indexes if self._states[i].available(now)]
        return available or indexes

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        errors: list[str] = []
        with self._lock:
            now = self._clock()
            indexes = self._ordered_indexes(now)
        for index in indexes:
            state = self._states[index]
            try:
                result = self._clients[state.url].call(method, params)
            except BitcoinRpcError as exc:
                with self._lock:
                    state.failures += 1
                    state.last_failure_at = self._clock()
                    state.last_error = str(exc)
                    if state.failures >= self.failure_threshold:
                        state.circuit_open_until = self._clock() + self.cooldown_seconds
                errors.append(f"{state.url}: {exc}")
                continue
            with self._lock:
                state.successes += 1
                state.failures = 0
                state.circuit_open_until = 0.0
                state.last_error = None
                state.last_success_at = self._clock()
                self._active_index = index
            return result
        raise BitcoinRpcError("All Bitcoin RPC endpoints failed: " + "; ".join(errors))

    def get_block_template(self) -> dict[str, Any]:
        result = self.call(
            "getblocktemplate",
            [{"rules": ["segwit"], "capabilities": ["coinbasetxn", "workid"]}],
        )
        if not isinstance(result, dict):
            raise BitcoinRpcError("getblocktemplate returned a non-object result")
        return result

    def get_blockchain_info(self) -> dict[str, Any]:
        result = self.call("getblockchaininfo")
        if not isinstance(result, dict):
            raise BitcoinRpcError("getblockchaininfo returned a non-object result")
        return result

    def submit_block(self, block_hex: str, work_id: str | None = None) -> str | None:
        params: list[Any] = [block_hex]
        if work_id is not None:
            params.append({"workid": work_id})
        result = self.call("submitblock", params)
        return None if result is None else str(result)

    def get_block(self, block_hash: str, verbosity: int = 1) -> Any:
        return self.call("getblock", [block_hash, verbosity])

    def status(self) -> dict[str, Any]:
        now = self._clock()
        with self._lock:
            endpoints = [
                {
                    "url": state.url,
                    "active": index == self._active_index,
                    "available": state.available(now),
                    "failures": state.failures,
                    "successes": state.successes,
                    "circuitOpenSeconds": max(0.0, state.circuit_open_until - now),
                    "lastError": state.last_error,
                    "lastSuccessAt": state.last_success_at,
                    "lastFailureAt": state.last_failure_at,
                }
                for index, state in enumerate(self._states)
            ]
        return {"activeEndpoint": self.url, "endpointCount": len(endpoints), "endpoints": endpoints}

    def probe(self) -> dict[str, Any]:
        info = self.get_blockchain_info()
        status = self.status()
        status["chain"] = info.get("chain")
        status["blocks"] = info.get("blocks")
        status["headers"] = info.get("headers")
        status["initialBlockDownload"] = info.get("initialblockdownload")
        return status
