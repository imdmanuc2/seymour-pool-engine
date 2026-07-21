import asyncio
import json
from typing import Any

import pytest

from seymour_pool_engine.config.stratum import StratumSettings
from seymour_pool_engine.stratum.server import StratumServer


class MemoryRepository:
    def create_session(self, session: Any) -> None:
        pass

    def update_session(self, session: Any) -> None:
        pass

    def close_session(self, session_id: Any, reason: str) -> None:
        pass

    def record_job(self, job: Any) -> None:
        pass

    def record_submission(self, *args: Any) -> None:
        pass


@pytest.mark.asyncio
async def test_tcp_subscribe_and_authorize() -> None:
    settings = StratumSettings(host="127.0.0.1", port=0, idle_timeout_seconds=2)
    server = StratumServer(settings, MemoryRepository())  # type: ignore[arg-type]
    await server.start()
    assert server._server is not None
    host, port = server._server.sockets[0].getsockname()[:2]
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(b'{"id":1,"method":"mining.subscribe","params":["pytest"]}\n')
    await writer.drain()
    assert json.loads(await reader.readline())["id"] == 1
    writer.write(b'{"id":2,"method":"mining.authorize","params":["wallet.worker","x"]}\n')
    await writer.drain()
    assert json.loads(await reader.readline())["result"] is True
    assert json.loads(await reader.readline())["method"] == "mining.set_difficulty"
    assert json.loads(await reader.readline())["method"] == "mining.notify"
    writer.close()
    await writer.wait_closed()
    await server.stop()
