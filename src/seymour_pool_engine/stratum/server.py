import asyncio
import logging
from contextlib import suppress

from seymour_pool_engine.config.stratum import StratumSettings, get_stratum_settings
from seymour_pool_engine.engines.protocol.codec import (
    ProtocolError,
    decode_request,
    encode,
    error_response,
)
from seymour_pool_engine.engines.session.extranonce import ExtranonceAllocator
from seymour_pool_engine.engines.session.models import StratumSession
from seymour_pool_engine.repositories.stratum_repository import StratumRepository
from seymour_pool_engine.stratum.dispatcher import StratumDispatcher

logger = logging.getLogger(__name__)


class StratumServer:
    def __init__(
        self,
        settings: StratumSettings | None = None,
        repository: StratumRepository | None = None,
    ) -> None:
        self.settings = settings or get_stratum_settings()
        self.repository = repository or StratumRepository()
        self.dispatcher = StratumDispatcher(self.repository)
        self.extranonces = ExtranonceAllocator()
        self._server: asyncio.AbstractServer | None = None
        self._connections = 0
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._client,
            self.settings.host,
            self.settings.port,
            limit=self.settings.max_line_bytes + 1,
        )

    async def serve_forever(self) -> None:
        await self.start()
        assert self._server is not None
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _send(self, writer, session, message) -> None:
        writer.write(encode(message))
        await writer.drain()
        session.messages_sent += 1

    async def _client(self, reader, writer) -> None:
        async with self._lock:
            if self._connections >= self.settings.max_connections:
                writer.close()
                await writer.wait_closed()
                return
            self._connections += 1
        peer = writer.get_extra_info("peername") or ("unknown", 0)
        s = StratumSession(
            str(peer[0]),
            int(peer[1]),
            self.extranonces.allocate(),
            self.settings.extranonce2_size,
            self.settings.default_difficulty,
        )
        reason = "client disconnected"
        self.repository.create_session(s)
        try:
            while True:
                try:
                    raw = await asyncio.wait_for(
                        reader.readline(), self.settings.idle_timeout_seconds
                    )
                except TimeoutError:
                    reason = "idle timeout"
                    break
                if not raw:
                    break
                s.messages_received += 1
                try:
                    req = decode_request(raw, self.settings.max_line_bytes)
                    result = self.dispatcher.dispatch(s, req)
                    if result.error:
                        await self._send(writer, s, error_response(req.request_id, *result.error))
                    else:
                        for msg in result.messages:
                            await self._send(writer, s, msg)
                except ProtocolError as exc:
                    await self._send(writer, s, error_response(None, exc.code, exc.message))
                self.repository.update_session(s)
        except (ConnectionError, asyncio.IncompleteReadError):
            reason = "connection lost"
        finally:
            self.repository.close_session(s.session_id, reason)
            async with self._lock:
                self._connections -= 1
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()
