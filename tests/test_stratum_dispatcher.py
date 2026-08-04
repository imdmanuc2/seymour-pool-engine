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
