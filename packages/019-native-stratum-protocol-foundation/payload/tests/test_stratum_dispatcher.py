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


def test_authorize_sends_job() -> None:
    repo = MemoryRepository()
    dispatcher = StratumDispatcher(repo)  # type: ignore[arg-type]
    session = make_session()
    result = dispatcher.dispatch(session, RpcRequest(2, "mining.authorize", ["wallet.worker", "x"]))
    assert result.error is None
    assert session.authorized
    assert result.messages[1]["method"] == "mining.set_difficulty"
    assert result.messages[2]["method"] == "mining.notify"
    assert len(repo.jobs) == 1


def test_submit_requires_authorization() -> None:
    repo = MemoryRepository()
    result = StratumDispatcher(repo).dispatch(  # type: ignore[arg-type]
        make_session(),
        RpcRequest(3, "mining.submit", ["wallet.worker", "job", "00", "00", "00"]),
    )
    assert result.error and result.error[0] == 24
