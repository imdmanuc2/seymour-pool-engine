import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RpcRequest:
    request_id: int | str | None
    method: str
    params: list[Any]


class ProtocolError(ValueError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def decode_request(raw: bytes, max_bytes: int = 65536) -> RpcRequest:
    if len(raw) > max_bytes:
        raise ProtocolError(-32600, "request too large")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(-32700, "parse error") from exc
    if not isinstance(value, dict):
        raise ProtocolError(-32600, "request must be an object")
    method, params = value.get("method"), value.get("params", [])
    if not isinstance(method, str) or not method:
        raise ProtocolError(-32600, "invalid method")
    if not isinstance(params, list):
        raise ProtocolError(-32602, "params must be an array")
    return RpcRequest(value.get("id"), method, params)


def encode(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode() + b"\n"


def response(request_id: int | str | None, result: Any) -> dict[str, Any]:
    return {"id": request_id, "result": result, "error": None}


def error_response(request_id: int | str | None, code: int, message: str) -> dict[str, Any]:
    return {"id": request_id, "result": None, "error": [code, message, None]}


def notification(method: str, params: list[Any]) -> dict[str, Any]:
    return {"id": None, "method": method, "params": params}
