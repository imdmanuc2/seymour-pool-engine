from typing import Any

from seymour_pool_engine.engines.jobs.synthetic import create_synthetic_job
from seymour_pool_engine.engines.protocol.codec import (
    RpcRequest,
    notification,
    response,
)
from seymour_pool_engine.engines.session.models import StratumSession
from seymour_pool_engine.repositories.stratum_repository import StratumRepository


class DispatchResult:
    def __init__(
        self, messages: list[dict[str, Any]], error: tuple[int, str] | None = None
    ) -> None:
        self.messages = messages
        self.error = error


class StratumDispatcher:
    def __init__(self, repository: StratumRepository) -> None:
        self.repository = repository

    def dispatch(self, s: StratumSession, r: RpcRequest) -> DispatchResult:
        if r.method == "mining.subscribe":
            s.user_agent = r.params[0] if r.params and isinstance(r.params[0], str) else None
            s.subscribed = True
            sid = str(s.session_id)
            result = [
                [["mining.set_difficulty", sid], ["mining.notify", sid]],
                s.extranonce1,
                s.extranonce2_size,
            ]
            return DispatchResult([response(r.request_id, result)])
        if r.method == "mining.authorize":
            if not r.params or not isinstance(r.params[0], str) or not r.params[0].strip():
                return DispatchResult([], (24, "worker name required"))
            s.worker_name = r.params[0].strip()
            s.authorized = True
            job = create_synthetic_job()
            self.repository.record_job(job)
            return DispatchResult(
                [
                    response(r.request_id, True),
                    notification("mining.set_difficulty", [s.difficulty]),
                    notification("mining.notify", job.notify_params()),
                ]
            )
        if r.method == "mining.configure":
            requested = r.params[0] if r.params and isinstance(r.params[0], list) else []
            return DispatchResult([response(r.request_id, {str(x): False for x in requested})])
        if r.method == "mining.extranonce.subscribe":
            return DispatchResult([response(r.request_id, True)])
        if r.method == "mining.submit":
            s.submissions_received += 1
            if not s.authorized:
                return DispatchResult([], (24, "unauthorized worker"))
            if len(r.params) < 5 or r.params[0] != s.worker_name:
                return DispatchResult([], (20, "invalid submission"))
            self.repository.record_submission(s, r.params)
            return DispatchResult([response(r.request_id, True)])
        return DispatchResult([], (20, f"unsupported method: {r.method}"))
