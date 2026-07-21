from __future__ import annotations

import itertools
from typing import Any

import httpx


class BitcoinRpcError(RuntimeError):
    """Raised when Bitcoin Core returns an RPC or transport error."""


class BitcoinRpcClient:
    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.url = url
        self.auth = (username, password) if username is not None and password is not None else None
        self.timeout_seconds = timeout_seconds
        self._ids = itertools.count(1)

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": next(self._ids),
            "method": method,
            "params": params or [],
        }
        try:
            response = httpx.post(
                self.url,
                json=payload,
                auth=self.auth,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise BitcoinRpcError(f"Bitcoin RPC transport failure: {exc}") from exc
        if body.get("error"):
            raise BitcoinRpcError(f"Bitcoin RPC {method} failed: {body['error']}")
        return body.get("result")

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
        if result is None:
            return None
        return str(result)

    def get_block(self, block_hash: str, verbosity: int = 1) -> Any:
        return self.call("getblock", [block_hash, verbosity])
