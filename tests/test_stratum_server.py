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
    subscribe_response = json.loads(await reader.readline())
    assert subscribe_response["id"] == 1
    assert subscribe_response["result"][0] == [
        [
            "mining.notify",
            subscribe_response["result"][0][0][1],
        ],
    ]

    writer.write(b'{"id":2,"method":"mining.authorize","params":["wallet.worker","x"]}\n')
    await writer.drain()

    authorize_response = json.loads(await reader.readline())
    assert authorize_response["id"] == 2
    assert authorize_response["result"] is True

    difficulty_message = json.loads(await reader.readline())
    assert difficulty_message["method"] == "mining.set_difficulty"

    notify_message = json.loads(await reader.readline())
    assert notify_message["method"] == "mining.notify"
    writer.close()
    await writer.wait_closed()
    await server.stop()


@pytest.mark.asyncio
async def test_blocking_repository_does_not_starve_second_client() -> None:
    import time

    class SlowRepository(MemoryRepository):
        def update_session(self, session: Any) -> None:
            time.sleep(0.2)

    settings = StratumSettings(
        host="127.0.0.1",
        port=0,
        idle_timeout_seconds=2,
        processing_workers=4,
        processing_queue_limit=32,
    )
    server = StratumServer(settings, SlowRepository())  # type: ignore[arg-type]
    await server.start()
    assert server._server is not None
    host, port = server._server.sockets[0].getsockname()[:2]

    reader1, writer1 = await asyncio.open_connection(host, port)
    reader2, writer2 = await asyncio.open_connection(host, port)

    writer1.write(b'{"id":1,"method":"mining.subscribe","params":["one"]}\n')
    writer2.write(b'{"id":2,"method":"mining.subscribe","params":["two"]}\n')
    await asyncio.gather(writer1.drain(), writer2.drain())

    response1, response2 = await asyncio.wait_for(
        asyncio.gather(reader1.readline(), reader2.readline()),
        timeout=1.0,
    )
    assert json.loads(response1)["id"] == 1
    assert json.loads(response2)["id"] == 2

    writer1.close()
    writer2.close()
    await writer1.wait_closed()
    await writer2.wait_closed()
    await server.stop()
