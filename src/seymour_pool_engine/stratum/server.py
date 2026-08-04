import asyncio
import logging
from datetime import UTC, datetime
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from typing import Any

from seymour_pool_engine.config.stratum import (
    StratumSettings,
    get_stratum_settings,
)
from seymour_pool_engine.database.connections import (
    close_engine_pool,
    configure_engine_pool,
)
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
        self._owns_repository = repository is None
        self.repository = repository or StratumRepository()
        self.dispatcher = StratumDispatcher(
            self.repository,
            settings=self.settings,
        )
        self.extranonces = ExtranonceAllocator()

        self._server: asyncio.AbstractServer | None = None
        self._connections = 0
        self._lock = asyncio.Lock()
        self._processing_slots = asyncio.Semaphore(self.settings.processing_queue_limit)
        self._executor = ThreadPoolExecutor(
            max_workers=self.settings.processing_workers,
            thread_name_prefix="seymour-share",
        )
        self._processing_active = 0
        self._processing_high_water = 0

    async def start(self) -> None:
        logger.info(
            "Starting Stratum server host=%s port=%s "
            "idle_timeout_seconds=%s max_connections=%s "
            "max_line_bytes=%s default_difficulty=%s "
            "extranonce2_size=%s processing_workers=%s processing_queue_limit=%s",
            self.settings.host,
            self.settings.port,
            self.settings.idle_timeout_seconds,
            self.settings.max_connections,
            self.settings.max_line_bytes,
            self.settings.default_difficulty,
            self.settings.extranonce2_size,
            self.settings.processing_workers,
            self.settings.processing_queue_limit,
        )

        if self._owns_repository:
            configure_engine_pool(
                min_size=self.settings.database_pool_min_size,
                max_size=self.settings.database_pool_max_size,
                timeout=self.settings.database_pool_timeout_seconds,
            )

        self._server = await asyncio.start_server(
            self._client,
            self.settings.host,
            self.settings.port,
            limit=self.settings.max_line_bytes + 1,
        )

        sockets = self._server.sockets or []

        for sock in sockets:
            logger.info(
                "Stratum server listening on %s",
                sock.getsockname(),
            )

    async def serve_forever(self) -> None:
        await self.start()

        assert self._server is not None

        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        self._executor.shutdown(wait=True, cancel_futures=False)
        if self._owns_repository:
            await asyncio.to_thread(close_engine_pool)

    async def _run_blocking(self, function: Any, *args: Any) -> Any:
        """Run CPU/database work outside the socket-reading event loop."""
        async with self._processing_slots:
            self._processing_active += 1
            self._processing_high_water = max(
                self._processing_high_water,
                self._processing_active,
            )
            try:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    self._executor,
                    function,
                    *args,
                )
            finally:
                self._processing_active -= 1

    def ingestion_status(self) -> dict[str, int]:
        return {
            "processingActive": self._processing_active,
            "processingHighWater": self._processing_high_water,
            "processingWorkers": self.settings.processing_workers,
            "processingQueueLimit": self.settings.processing_queue_limit,
        }

    @staticmethod
    def _message_summary(message: Any) -> str:
        if not isinstance(message, dict):
            return repr(message)

        request_id = message.get("id")
        method = message.get("method")

        if method is not None:
            return (
                f"notification id={request_id!r} method={method!r} params={message.get('params')!r}"
            )

        if "error" in message and message.get("error") is not None:
            return f"response id={request_id!r} error={message.get('error')!r}"

        return f"response id={request_id!r} result={message.get('result')!r}"

    async def _send(
        self,
        writer: asyncio.StreamWriter,
        session: StratumSession,
        message: Any,
    ) -> None:
        logger.debug(
            "SEND session=%s worker=%s peer=%s:%s %s",
            session.session_id,
            session.worker_name or "-",
            session.remote_host,
            session.remote_port,
            self._message_summary(message),
        )

        payload = encode(message)

        logger.debug(
            "SEND RAW session=%s bytes=%r",
            session.session_id,
            payload,
        )

        writer.write(payload)
        await writer.drain()

        session.messages_sent += 1

    async def _client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        async with self._lock:
            if self._connections >= self.settings.max_connections:
                peer = writer.get_extra_info("peername") or ("unknown", 0)

                logger.warning(
                    "Rejecting Stratum connection peer=%s:%s "
                    "reason=max connections reached current=%s maximum=%s",
                    peer[0],
                    peer[1],
                    self._connections,
                    self.settings.max_connections,
                )

                writer.close()

                with suppress(Exception):
                    await writer.wait_closed()

                return

            self._connections += 1

        peer = writer.get_extra_info("peername") or ("unknown", 0)

        session = StratumSession(
            str(peer[0]),
            int(peer[1]),
            self.extranonces.allocate(),
            self.settings.extranonce2_size,
            self.settings.default_difficulty,
        )

        reason = "client disconnected"

        logger.info(
            "Stratum connection opened "
            "session=%s peer=%s:%s extranonce1=%s "
            "extranonce2_size=%s difficulty=%s "
            "idle_timeout_seconds=%s active_connections=%s",
            session.session_id,
            session.remote_host,
            session.remote_port,
            session.extranonce1,
            session.extranonce2_size,
            session.difficulty,
            self.settings.idle_timeout_seconds,
            self._connections,
        )

        await self._run_blocking(self.repository.create_session, session)

        try:
            while True:
                read_timeout = self.settings.idle_timeout_seconds

                if (
                    session.authorized
                    and session.submissions_received == 0
                    and session.authorized_at is not None
                ):
                    read_timeout = min(
                        read_timeout,
                        self.settings.no_share_recovery_seconds,
                    )

                try:
                    raw = await asyncio.wait_for(
                        reader.readline(),
                        timeout=read_timeout,
                    )
                except TimeoutError:
                    now = datetime.now(UTC)

                    if (
                        session.authorized
                        and session.submissions_received == 0
                        and session.authorized_at is not None
                    ):
                        no_share_seconds = (now - session.authorized_at).total_seconds()

                        if no_share_seconds >= self.settings.no_share_disconnect_seconds:
                            reason = "no-share startup recovery exhausted"

                            logger.warning(
                                "NO_SHARE_DISCONNECT "
                                "session=%s worker=%s peer=%s:%s "
                                "no_share_seconds=%.3f "
                                "messages_received=%s messages_sent=%s",
                                session.session_id,
                                session.worker_name or "-",
                                session.remote_host,
                                session.remote_port,
                                no_share_seconds,
                                session.messages_received,
                                session.messages_sent,
                            )

                            writer.close()

                            with suppress(Exception):
                                await writer.wait_closed()

                            break

                        if (
                            no_share_seconds >= self.settings.no_share_recovery_seconds
                            and not session.no_share_recovery_attempted
                        ):
                            recovery_messages = await self._run_blocking(
                                self.dispatcher.recovery_messages,
                                session,
                            )

                            for message in recovery_messages:
                                await self._send(
                                    writer,
                                    session,
                                    message,
                                )

                            session.no_share_recovery_attempted = True

                            logger.warning(
                                "NO_SHARE_RECOVERY "
                                "session=%s worker=%s peer=%s:%s "
                                "no_share_seconds=%.3f "
                                "difficulty=%s recovery_job=%s",
                                session.session_id,
                                session.worker_name or "-",
                                session.remote_host,
                                session.remote_port,
                                no_share_seconds,
                                session.difficulty,
                                recovery_messages[1]["params"][0],
                            )

                            await self._run_blocking(
                                self.repository.update_session,
                                session,
                            )

                            continue

                        # Keep checking the startup condition without
                        # applying the normal idle timeout yet.
                        continue

                    reason = "idle timeout"

                    logger.warning(
                        "Stratum idle timeout "
                        "session=%s worker=%s peer=%s:%s "
                        "idle_timeout_seconds=%s "
                        "messages_received=%s messages_sent=%s",
                        session.session_id,
                        session.worker_name or "-",
                        session.remote_host,
                        session.remote_port,
                        self.settings.idle_timeout_seconds,
                        session.messages_received,
                        session.messages_sent,
                    )

                    break

                if not raw:
                    reason = "client closed connection"

                    logger.info(
                        "Stratum client closed connection session=%s worker=%s peer=%s:%s",
                        session.session_id,
                        session.worker_name or "-",
                        session.remote_host,
                        session.remote_port,
                    )

                    break

                session.messages_received += 1

                logger.debug(
                    "RECV RAW session=%s peer=%s:%s bytes=%r",
                    session.session_id,
                    session.remote_host,
                    session.remote_port,
                    raw,
                )

                try:
                    request = decode_request(
                        raw,
                        self.settings.max_line_bytes,
                    )

                    logger.debug(
                        "RECV session=%s worker=%s peer=%s:%s id=%r method=%s params=%r",
                        session.session_id,
                        session.worker_name or "-",
                        session.remote_host,
                        session.remote_port,
                        request.request_id,
                        request.method,
                        request.params,
                    )

                    result = await self._run_blocking(
                        self.dispatcher.dispatch,
                        session,
                        request,
                    )

                    if result.error:
                        await self._send(
                            writer,
                            session,
                            error_response(
                                request.request_id,
                                *result.error,
                            ),
                        )

                    for message in result.messages:
                        await self._send(
                            writer,
                            session,
                            message,
                        )

                    if result.close_connection:
                        reason = result.close_reason or "dispatcher requested connection close"

                        logger.warning(
                            "Stratum recovery closing connection "
                            "session=%s worker=%s peer=%s:%s "
                            "reason=%s",
                            session.session_id,
                            session.worker_name or "-",
                            session.remote_host,
                            session.remote_port,
                            reason,
                        )

                        await self._run_blocking(
                            self.repository.update_session,
                            session,
                        )

                        writer.close()

                        with suppress(Exception):
                            await writer.wait_closed()

                        break

                except ProtocolError as exc:
                    logger.warning(
                        "Stratum protocol error session=%s worker=%s peer=%s:%s code=%s message=%s",
                        session.session_id,
                        session.worker_name or "-",
                        session.remote_host,
                        session.remote_port,
                        exc.code,
                        exc.message,
                    )

                    await self._send(
                        writer,
                        session,
                        error_response(
                            None,
                            exc.code,
                            exc.message,
                        ),
                    )

                await self._run_blocking(self.repository.update_session, session)

        except asyncio.CancelledError:
            reason = "server task cancelled"

            logger.info(
                "Stratum connection task cancelled session=%s worker=%s peer=%s:%s",
                session.session_id,
                session.worker_name or "-",
                session.remote_host,
                session.remote_port,
            )

            raise

        except (ConnectionError, asyncio.IncompleteReadError) as exc:
            reason = "connection lost"

            logger.info(
                "Stratum connection lost session=%s worker=%s peer=%s:%s error=%s",
                session.session_id,
                session.worker_name or "-",
                session.remote_host,
                session.remote_port,
                exc,
            )

        except Exception:
            reason = "server error"

            logger.exception(
                "Unhandled Stratum client error session=%s worker=%s peer=%s:%s",
                session.session_id,
                session.worker_name or "-",
                session.remote_host,
                session.remote_port,
            )

        finally:
            await self._run_blocking(
                self.repository.close_session,
                session.session_id,
                reason,
            )

            async with self._lock:
                self._connections -= 1
                active_connections = self._connections

            writer.close()

            with suppress(Exception):
                await writer.wait_closed()

            logger.info(
                "Stratum connection closed "
                "session=%s worker=%s peer=%s:%s "
                "reason=%s messages_received=%s "
                "messages_sent=%s active_connections=%s",
                session.session_id,
                session.worker_name or "-",
                session.remote_host,
                session.remote_port,
                reason,
                session.messages_received,
                session.messages_sent,
                active_connections,
            )
