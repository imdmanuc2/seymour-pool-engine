import hashlib
import logging
from typing import Any

from seymour_pool_engine.config.stratum import (
    StratumSettings,
    get_stratum_settings,
)
from seymour_pool_engine.engines.jobs.synthetic import create_synthetic_job
from seymour_pool_engine.engines.protocol.codec import (
    RpcRequest,
    notification,
    response,
)
from seymour_pool_engine.engines.session.models import StratumSession
from seymour_pool_engine.engines.shares.validator import (
    ShareValidationError,
    validate_share,
)
from seymour_pool_engine.engines.vardiff import VarDiffController
from seymour_pool_engine.repositories.stratum_repository import StratumRepository
from seymour_pool_engine.services.block_submission_service import (
    BlockSubmissionService,
)
from seymour_pool_engine.services.template_job_service import (
    TemplateJobService,
)

logger = logging.getLogger(__name__)


class DispatchResult:
    def __init__(
        self,
        messages: list[dict[str, Any]],
        error: tuple[int, str] | None = None,
    ) -> None:
        self.messages = messages
        self.error = error


SUPPORTED_VERSION_ROLLING_MASK = 0x1FFFE000


class StratumDispatcher:
    def __init__(
        self,
        repository: StratumRepository,
        job_service: TemplateJobService | None = None,
        block_service: BlockSubmissionService | None = None,
        vardiff: VarDiffController | None = None,
        settings: StratumSettings | None = None,
    ) -> None:
        self.repository = repository
        self.job_service = job_service
        self.block_service = block_service
        self.vardiff = vardiff or VarDiffController()
        self.settings = settings or get_stratum_settings()

    @staticmethod
    def _remember_job_difficulty(
        session: StratumSession,
        job_id: str,
        difficulty: float,
    ) -> None:
        session.job_difficulties[str(job_id)] = float(difficulty)

        # Retain enough recent jobs for delayed submissions while preventing
        # an unbounded per-session mapping.
        while len(session.job_difficulties) > 16:
            oldest_job_id = next(iter(session.job_difficulties))
            del session.job_difficulties[oldest_job_id]

    def _refresh_job(self, *, clean_jobs: bool):
        if self.job_service is not None or hasattr(self.repository, "latest_job"):
            service = self.job_service or TemplateJobService(repository=self.repository)
            return service.refresh(clean_jobs=clean_jobs)

        job = create_synthetic_job()
        self.repository.record_job(job)
        return job

    def dispatch(
        self,
        s: StratumSession,
        r: RpcRequest,
    ) -> DispatchResult:
        if r.method == "mining.subscribe":
            s.user_agent = r.params[0] if r.params and isinstance(r.params[0], str) else None
            s.subscribed = True

            sid = str(s.session_id)
            result = [
                [
                    ["mining.notify", sid],
                ],
                s.extranonce1,
                s.extranonce2_size,
            ]

            logger.info(
                "CKPOOL_COMPAT subscribed session=%s extranonce1=%s extranonce2_size=%s",
                s.session_id,
                s.extranonce1,
                s.extranonce2_size,
            )

            # Do not issue mining work during subscribe.
            #
            # Avalon firmware may send:
            #   mining.subscribe
            #   mining.configure
            #   mining.authorize
            #
            # Work is issued exactly once after authorization so the
            # miner never receives two competing clean startup jobs.
            return DispatchResult(
                [
                    response(r.request_id, result),
                ]
            )

        if r.method == "mining.authorize":
            if not r.params or not isinstance(r.params[0], str) or not r.params[0].strip():
                return DispatchResult(
                    [],
                    (24, "worker name required"),
                )

            s.worker_name = r.params[0].strip()
            s.authorized = True

            cpu_suffix = self.settings.cpu_worker_suffix.strip()

            if cpu_suffix and s.worker_name.endswith(cpu_suffix):
                s.difficulty = self.settings.cpu_difficulty
                s.minimum_difficulty = self.settings.cpu_difficulty

                logger.info(
                    "CPU_DIFFICULTY worker=%s difficulty=%s minimum_difficulty=%s",
                    s.worker_name,
                    s.difficulty,
                    s.minimum_difficulty,
                )
            else:
                s.minimum_difficulty = self.vardiff.config.min_difficulty

            logger.info(
                "CKPOOL_COMPAT authorized session=%s worker=%s",
                s.session_id,
                s.worker_name,
            )

            job = self._refresh_job(clean_jobs=True)
            notify_params = job.notify_params()

            self._remember_job_difficulty(
                s,
                job.job_id,
                s.difficulty,
            )

            logger.info(
                "JOB worker=%s job=%s prevhash=%s version=%s "
                "nbits=%s ntime=%s clean_jobs=%s branches=%d "
                "extranonce1=%s extranonce2_size=%s",
                s.worker_name,
                notify_params[0],
                notify_params[1],
                notify_params[5],
                notify_params[6],
                notify_params[7],
                notify_params[8],
                len(notify_params[4]),
                s.extranonce1,
                s.extranonce2_size,
            )
            logger.info(
                "JOB_DATA job=%s coinbase1=%s coinbase2=%s merkle_branches=%s",
                notify_params[0],
                notify_params[2],
                notify_params[3],
                notify_params[4],
            )

            # Build one deterministic diagnostic candidate using the
            # session extranonce1 and an all-zero extranonce2. This is
            # logging only and does not modify the job sent to miners.
            diagnostic_extranonce2 = "00" * s.extranonce2_size
            diagnostic_coinbase_hex = (
                notify_params[2] + s.extranonce1 + diagnostic_extranonce2 + notify_params[3]
            )
            diagnostic_coinbase = bytes.fromhex(diagnostic_coinbase_hex)
            diagnostic_coinbase_hash = hashlib.sha256(
                hashlib.sha256(diagnostic_coinbase).digest()
            ).digest()

            diagnostic_merkle_root = diagnostic_coinbase_hash

            for diagnostic_branch_hex in notify_params[4]:
                diagnostic_branch = bytes.fromhex(diagnostic_branch_hex)
                diagnostic_merkle_root = hashlib.sha256(
                    hashlib.sha256(diagnostic_merkle_root + diagnostic_branch).digest()
                ).digest()

            diagnostic_prevhash = bytes.fromhex(notify_params[1])
            diagnostic_prevhash_header = b"".join(
                diagnostic_prevhash[index : index + 4][::-1]
                for index in range(
                    0,
                    len(diagnostic_prevhash),
                    4,
                )
            )

            diagnostic_header = (
                int(
                    notify_params[5],
                    16,
                ).to_bytes(4, "little")
                + diagnostic_prevhash_header
                + diagnostic_merkle_root
                + int(
                    notify_params[7],
                    16,
                ).to_bytes(4, "little")
                + int(
                    notify_params[6],
                    16,
                ).to_bytes(4, "little")
                + (0).to_bytes(4, "little")
            )
            diagnostic_header_hash = hashlib.sha256(
                hashlib.sha256(diagnostic_header).digest()
            ).digest()

            logger.info(
                "JOB_DIAGNOSTICS job=%s extranonce1=%s extranonce2=%s coinbase=%s",
                notify_params[0],
                s.extranonce1,
                diagnostic_extranonce2,
                diagnostic_coinbase_hex,
            )
            logger.info(
                "JOB_DIAGNOSTICS_HASHES job=%s "
                "coinbase_hash_internal=%s coinbase_txid=%s "
                "merkle_root_internal=%s "
                "merkle_root_display=%s",
                notify_params[0],
                diagnostic_coinbase_hash.hex(),
                diagnostic_coinbase_hash[::-1].hex(),
                diagnostic_merkle_root.hex(),
                diagnostic_merkle_root[::-1].hex(),
            )
            logger.info(
                "JOB_DIAGNOSTICS_HEADER job=%s header=%s header_hash_internal=%s header_hash=%s",
                notify_params[0],
                diagnostic_header.hex(),
                diagnostic_header_hash.hex(),
                diagnostic_header_hash[::-1].hex(),
            )

            logger.info(
                "JOB_TEMPLATE "
                "job=%s "
                "height=%s "
                "coinbase_value=%s "
                "tx_count=%s "
                "prevhash_raw=%s "
                "version=%s "
                "ntime=%s "
                "nbits=%s",
                notify_params[0],
                getattr(job, "template_height", None),
                getattr(job, "coinbase_value", None),
                getattr(job, "transaction_count", None),
                getattr(job, "previous_block_hash", None),
                notify_params[5],
                notify_params[7],
                notify_params[6],
            )

            if hasattr(job, "merkle_branches"):
                logger.info(
                    "JOB_TEMPLATE_MERKLE job=%s branches=%d",
                    notify_params[0],
                    len(job.merkle_branches),
                )

                for index, branch in enumerate(job.merkle_branches):
                    logger.info(
                        "MERKLE_BRANCH %02d %s",
                        index,
                        branch,
                    )

            return DispatchResult(
                [
                    response(r.request_id, True),
                    notification(
                        "mining.set_difficulty",
                        [s.difficulty],
                    ),
                    notification(
                        "mining.notify",
                        notify_params,
                    ),
                ]
            )

        if r.method == "mining.configure":
            requested = r.params[0] if r.params and isinstance(r.params[0], list) else []
            options = r.params[1] if len(r.params) > 1 and isinstance(r.params[1], dict) else {}

            result = {str(extension): False for extension in requested}

            if "version-rolling" in requested:
                requested_mask = options.get(
                    "version-rolling.mask",
                    "ffffffff",
                )

                try:
                    requested_mask_value = int(
                        str(requested_mask),
                        16,
                    )
                except (TypeError, ValueError):
                    requested_mask_value = 0

                negotiated_mask = requested_mask_value & SUPPORTED_VERSION_ROLLING_MASK

                if negotiated_mask:
                    normalized_mask = f"{negotiated_mask:08x}"

                    s.version_rolling = True
                    s.version_rolling_mask = normalized_mask

                    result["version-rolling"] = True
                    result["version-rolling.mask"] = normalized_mask

                    logger.info(
                        "VERSION_ROLLING requested_mask=%s supported_mask=%08x negotiated_mask=%s",
                        requested_mask,
                        SUPPORTED_VERSION_ROLLING_MASK,
                        normalized_mask,
                    )
                else:
                    s.version_rolling = False
                    s.version_rolling_mask = None

                    logger.info(
                        "VERSION_ROLLING rejected requested_mask=%s supported_mask=%08x",
                        requested_mask,
                        SUPPORTED_VERSION_ROLLING_MASK,
                    )

            return DispatchResult([response(r.request_id, result)])

        if r.method == "mining.extranonce.subscribe":
            return DispatchResult([response(r.request_id, True)])

        if r.method == "mining.submit":
            s.submissions_received += 1

            if not s.authorized:
                return DispatchResult(
                    [],
                    (24, "unauthorized worker"),
                )

            if len(r.params) < 5 or r.params[0] != s.worker_name:
                return DispatchResult(
                    [],
                    (20, "invalid submission"),
                )

            submitted_job_id = str(r.params[1])

            assigned_difficulty = s.job_difficulties.get(submitted_job_id)

            if assigned_difficulty is None:
                logger.info(
                    "STALE_SESSION_JOB worker=%s session=%s submitted_job=%s issued_jobs=%s",
                    s.worker_name,
                    s.session_id,
                    submitted_job_id,
                    list(s.job_difficulties),
                )

                return DispatchResult(
                    [],
                    (21, "stale or unknown job"),
                )

            job = self.repository.get_job(submitted_job_id)

            if job is None:
                return DispatchResult(
                    [],
                    (21, "stale or unknown job"),
                )

            submitted_version_bits = str(r.params[5]) if len(r.params) > 5 else None

            logger.debug(
                "SUBMIT worker=%s job=%s en2=%s ntime=%s nonce=%s version=%s",
                r.params[0],
                r.params[1],
                r.params[2],
                r.params[3],
                r.params[4],
                submitted_version_bits,
            )

            try:
                result = validate_share(
                    job=job,
                    extranonce1=s.extranonce1,
                    extranonce2=str(r.params[2]),
                    submitted_ntime=str(r.params[3]),
                    nonce=str(r.params[4]),
                    difficulty=assigned_difficulty,
                    extranonce2_size=s.extranonce2_size,
                    submitted_version_bits=submitted_version_bits,
                    version_rolling_mask=(s.version_rolling_mask if s.version_rolling else None),
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

                return DispatchResult(
                    [],
                    (20, exc.message),
                )

            inserted = self.repository.record_validated_submission(
                s,
                r.params,
                accepted=result.accepted,
                reject_reason=(None if result.accepted else "low-difficulty-share"),
                share_hash=result.hash_hex,
                share_difficulty=float(result.achieved_difficulty),
                block_candidate=result.block_candidate,
                header_hex=result.header_hex,
            )

            if not inserted:
                return DispatchResult(
                    [],
                    (22, "duplicate share"),
                )

            if not result.accepted:
                return DispatchResult(
                    [],
                    (23, "low difficulty share"),
                )

            decision = self.vardiff.observe(s)
            difficulty_message = None
            retarget_job_message = None

            if decision.changed:
                self.repository.record_difficulty_change(
                    s,
                    decision.old_difficulty,
                    decision.observed_share_seconds,
                    self.vardiff.config.target_share_seconds,
                    decision.reason,
                )

                difficulty_message = notification(
                    "mining.set_difficulty",
                    [s.difficulty],
                )

                retarget_job = self._refresh_job(clean_jobs=False)
                self._remember_job_difficulty(
                    s,
                    retarget_job.job_id,
                    s.difficulty,
                )

                retarget_job_message = notification(
                    "mining.notify",
                    retarget_job.notify_params(),
                )

                logger.info(
                    "VARDIFF_JOB worker=%s old_difficulty=%s new_difficulty=%s job=%s",
                    s.worker_name,
                    decision.old_difficulty,
                    decision.new_difficulty,
                    retarget_job.job_id,
                )

            if result.block_candidate:
                template = self.repository.get_template(job.template_height)

                if template is None:
                    return DispatchResult(
                        [],
                        (20, "block template unavailable"),
                    )

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
                        [],
                        (
                            20,
                            f"block submission rejected: {submission.error}",
                        ),
                    )

            messages = [response(r.request_id, True)]

            if difficulty_message is not None:
                messages.append(difficulty_message)

            if retarget_job_message is not None:
                messages.append(retarget_job_message)

            return DispatchResult(messages)

        return DispatchResult(
            [],
            (20, f"unsupported method: {r.method}"),
        )
