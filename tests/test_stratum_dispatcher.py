from typing import Any

from seymour_pool_engine.engines.protocol.codec import RpcRequest
from seymour_pool_engine.engines.session.models import StratumSession
from seymour_pool_engine.stratum.dispatcher import StratumDispatcher


class MemoryRepository:
    def __init__(self) -> None:
        self.jobs: list[Any] = []
        self.submissions: list[Any] = []

    def record_job(self, job: Any) -> None:
        self.jobs.append(job)

    def get_job(self, job_id: str) -> Any | None:
        for job in reversed(self.jobs):
            if job.job_id == job_id:
                return job
        return None

    def record_submission(self, *args: Any) -> None:
        self.submissions.append(args)


def make_session() -> StratumSession:
    return StratumSession("127.0.0.1", 1234, "01020304", 4, 1.0)


def test_subscribe() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    result = dispatcher.dispatch(session, RpcRequest(1, "mining.subscribe", ["miner"]))
    assert result.error is None
    assert session.subscribed


def test_authorize_returns_success() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    result = dispatcher.dispatch(session, RpcRequest(2, "mining.authorize", ["wallet.worker", "x"]))
    assert result.error is None
    assert session.authorized
    assert len(result.messages) == 3

    authorize_response = result.messages[0]
    assert authorize_response["id"] == 2
    assert authorize_response["result"] is True
    assert authorize_response["error"] is None

    difficulty_message = result.messages[1]
    assert difficulty_message["id"] is None
    assert difficulty_message["method"] == "mining.set_difficulty"

    notify_message = result.messages[2]
    assert notify_message["id"] is None
    assert notify_message["method"] == "mining.notify"


def test_submit_requires_authorization() -> None:
    repo = MemoryRepository()
    result = StratumDispatcher(repo).dispatch(  # type: ignore[arg-type]
        make_session(),
        RpcRequest(3, "mining.submit", ["wallet.worker", "job", "00", "00", "00"]),
    )
    assert result.error and result.error[0] == 24


def test_subscribe_does_not_issue_mining_job() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    session.difficulty = 42.0

    result = dispatcher.dispatch(
        session,
        RpcRequest(
            1,
            "mining.subscribe",
            ["miner"],
        ),
    )

    assert result.error is None
    assert len(result.messages) == 1
    assert result.messages[0]["id"] == 1
    assert repo.jobs == []
    assert session.job_difficulties == {}


def test_authorize_records_job_difficulty() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    session.difficulty = 84.0

    result = dispatcher.dispatch(
        session,
        RpcRequest(
            2,
            "mining.authorize",
            ["wallet.worker", "x"],
        ),
    )

    assert result.error is None
    assert len(repo.jobs) == 1

    job = repo.jobs[0]
    assert session.job_difficulties[job.job_id] == 84.0


def test_submit_rejects_job_not_issued_to_session() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    session.worker_name = "wallet.worker"
    session.authorized = True

    result = dispatcher.dispatch(
        session,
        RpcRequest(
            3,
            "mining.submit",
            [
                "wallet.worker",
                "old-global-job",
                "00000000",
                "00000000",
                "00000000",
            ],
        ),
    )

    assert result.error == (21, "stale or unknown job")


def test_stale_job_third_submission_issues_clean_recovery_job() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    session.worker_name = "wallet.worker"
    session.authorized = True
    session.difficulty = 42.0

    results = []

    for request_id in range(1, 4):
        results.append(
            dispatcher.dispatch(
                session,
                RpcRequest(
                    request_id,
                    "mining.submit",
                    [
                        "wallet.worker",
                        "old-global-job",
                        "0000000000000000",
                        "00000000",
                        "00000000",
                    ],
                ),
            )
        )

    assert results[0].error == (21, "stale or unknown job")
    assert results[0].messages == []
    assert results[0].close_connection is False

    assert results[1].error == (21, "stale or unknown job")
    assert results[1].messages == []
    assert results[1].close_connection is False

    recovery = results[2]

    assert recovery.error == (21, "stale or unknown job")
    assert recovery.close_connection is False
    assert len(recovery.messages) == 2

    assert recovery.messages[0]["method"] == "mining.set_difficulty"
    assert recovery.messages[0]["params"] == [42.0]

    assert recovery.messages[1]["method"] == "mining.notify"
    assert recovery.messages[1]["params"][-1] is True

    recovery_job_id = recovery.messages[1]["params"][0]

    assert session.job_difficulties[recovery_job_id] == 42.0
    assert session.stale_job_count == 3
    assert session.stale_job_recovery_attempted is True


def test_stale_job_fifth_submission_requests_disconnect() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    session.worker_name = "wallet.worker"
    session.authorized = True
    session.difficulty = 42.0

    final_result = None

    for request_id in range(1, 6):
        final_result = dispatcher.dispatch(
            session,
            RpcRequest(
                request_id,
                "mining.submit",
                [
                    "wallet.worker",
                    "old-global-job",
                    "0000000000000000",
                    "00000000",
                    "00000000",
                ],
            ),
        )

    assert final_result is not None
    assert final_result.error == (21, "stale or unknown job")
    assert final_result.close_connection is True
    assert final_result.close_reason == "stale job recovery threshold exceeded"
    assert session.stale_job_count == 5


def test_valid_session_job_resets_stale_recovery_state() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    session.worker_name = "wallet.worker"
    session.authorized = True
    session.stale_job_count = 4
    session.stale_job_recovery_attempted = True

    # Mark the job as issued to this session without storing it in the
    # repository. Recognizing the session job must clear stale recovery
    # state before repository lookup or share validation occurs.
    known_job_id = "known-session-job"
    session.job_difficulties[known_job_id] = session.difficulty

    result = dispatcher.dispatch(
        session,
        RpcRequest(
            99,
            "mining.submit",
            [
                "wallet.worker",
                known_job_id,
                "00000000",
                "00000000",
                "00000000",
            ],
        ),
    )

    assert result.error == (21, "stale or unknown job")
    assert result.close_connection is False
    assert session.stale_job_count == 0
    assert session.stale_job_window_started_at is None
    assert session.stale_job_recovery_attempted is False


def test_recovery_messages_issue_clean_job_at_session_difficulty() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    session.worker_name = "wallet.worker"
    session.authorized = True
    session.difficulty = 84.0

    messages = dispatcher.recovery_messages(
        session,
        clean_jobs=True,
    )

    assert len(messages) == 2
    assert messages[0]["method"] == "mining.set_difficulty"
    assert messages[0]["params"] == [84.0]

    assert messages[1]["method"] == "mining.notify"
    assert messages[1]["params"][-1] is True

    job_id = messages[1]["params"][0]
    assert session.job_difficulties[job_id] == 84.0


def test_authorize_initializes_no_share_recovery_state() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    session.no_share_recovery_attempted = True

    result = dispatcher.dispatch(
        session,
        RpcRequest(
            500,
            "mining.authorize",
            ["wallet.worker", "x"],
        ),
    )

    assert result.error is None
    assert session.authorized is True
    assert session.authorized_at is not None
    assert session.no_share_recovery_attempted is False
