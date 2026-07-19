from typing import Any

import httpx


class MiningCoreRestClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def health(self) -> dict[str, Any]:
        candidates = ("/api/pools", "/api")
        last_error: Exception | None = None
        for path in candidates:
            try:
                response = httpx.get(
                    f"{self.base_url}{path}",
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                return {
                    "status": "online",
                    "summary": "MiningCore REST API is responding",
                    "details": {"endpoint": path, "httpStatus": response.status_code},
                }
            except Exception as exc:  # provider boundary must return safe diagnostics
                last_error = exc
        return {
            "status": "offline",
            "summary": "MiningCore REST API is not responding",
            "details": {"error": str(last_error) if last_error else "unknown error"},
        }
