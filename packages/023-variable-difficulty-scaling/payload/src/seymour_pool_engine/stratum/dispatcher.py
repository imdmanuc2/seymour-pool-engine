from typing import Any

from seymour_pool_engine.engines.jobs.synthetic import create_synthetic_job
from seymour_pool_engine.engines.protocol.codec import (
    RpcRequest,
    notification,
    response,
)
from seymour_pool_engine.engines.session.models import StratumSession
from seymour_pool_engine.engines.shares.validator import ShareValidationError, validate_share
from seymour_pool_engine.engines.vardiff import VarDiffController
from seymour_pool_engine.repositories.stratum_repository import StratumRepository
from seymour_pool_engine.services.block_submission_service import BlockSubmissionService
from seymour_pool_engine.services.template_job_service import TemplateJobService


class DispatchResult:
    def __init__(
        self, messages: list[dict[str, Any]], error: tuple[int, str] | None = None
    ) -> None:
        self.messages = messages
        self.error = error


class StratumDispatcher:
    def __init__(
        self,
        repository: StratumRepository,
        job_service: TemplateJobService | None = None,
        block_service: BlockSubmissionService | None = None,
        vardiff: VarDiffController | None = None,
    ) -> None:
        self.repository = repository
        self.job_service = job_service
        self.block_service = block_service
        self.vardiff = vardiff or VarDiffController()

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
            if self.job_service is not None or hasattr(self.repository, "latest_job"):
                service = self.job_service or TemplateJobService(repository=self.repository)
                job = service.latest() or service.refresh()
            else:
                # Preserve lightweight in-memory test repositories used by the protocol suite.
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
            job = self.repository.get_job(str(r.params[1]))
            if job is None:
                return DispatchResult([], (21, "stale or unknown job"))
            try:
                result = validate_share(
                    job=job,
                    extranonce1=s.extranonce1,
                    extranonce2=str(r.params[2]),
                    submitted_ntime=str(r.params[3]),
                    nonce=str(r.params[4]),
                    difficulty=s.difficulty,
                    extranonce2_size=s.extranonce2_size,
                )
            except ShareValidationError as exc:
                self.repository.record_validated_submission(
                    s,
                    r.params,
                    accepted=False,
                    reject_reason=exc.reason,
                    share_hash=None,
                    share_difficulty=None,
                    block_candidate=False,
                    header_hex=None,
                )
                return DispatchResult([], (20, exc.message))
            inserted = self.repository.record_validated_submission(
                s,
                r.params,
                accepted=result.accepted,
                reject_reason=None if result.accepted else "low-difficulty-share",
                share_hash=result.hash_hex,
                share_difficulty=float(result.achieved_difficulty),
                block_candidate=result.block_candidate,
                header_hex=result.header_hex,
            )
            if not inserted:
                return DispatchResult([], (22, "duplicate share"))
            if not result.accepted:
                return DispatchResult([], (23, "low difficulty share"))
            decision = self.vardiff.observe(s)
            difficulty_message = None
            if decision.changed:
                self.repository.record_difficulty_change(
                    s,
                    decision.old_difficulty,
                    decision.observed_share_seconds,
                    self.vardiff.config.target_share_seconds,
                    decision.reason,
                )
                difficulty_message = notification("mining.set_difficulty", [s.difficulty])
            if result.block_candidate:
                template = self.repository.get_template(job.template_height)
                if template is None:
                    return DispatchResult([], (20, "block template unavailable"))
                service = self.block_service or BlockSubmissionService()
                submission = service.submit_candidate(
                    job=job,
                    template=template,
                    validation=result,
                    extranonce1=s.extranonce1,
                    extranonce2=str(r.params[2]),
                )
                if not submission.accepted:
                    return DispatchResult(
                        [], (20, f"block submission rejected: {submission.error}")
                    )
            messages = [response(r.request_id, True)]
            if difficulty_message is not None:
                messages.append(difficulty_message)
            return DispatchResult(messages)
        return DispatchResult([], (20, f"unsupported method: {r.method}"))
