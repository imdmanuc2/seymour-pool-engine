from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from seymour_pool_engine.config import get_settings

_engine_pool: ConnectionPool | None = None
_engine_pool_lock = Lock()


def get_engine_pool(
    *,
    min_size: int = 2,
    max_size: int = 16,
    timeout: float = 5.0,
) -> ConnectionPool:
    """Return the process-wide engine database connection pool."""
    global _engine_pool
    if _engine_pool is None:
        with _engine_pool_lock:
            if _engine_pool is None:
                settings = get_settings()
                _engine_pool = ConnectionPool(
                    conninfo=settings.engine_database_url,
                    min_size=min_size,
                    max_size=max_size,
                    timeout=timeout,
                    kwargs={
                        "row_factory": dict_row,
                        "connect_timeout": 5,
                    },
                    open=True,
                    name="seymour-engine",
                )
    return _engine_pool


def configure_engine_pool(*, min_size: int, max_size: int, timeout: float) -> None:
    """Initialize the pool with Stratum runtime sizing before first use."""
    get_engine_pool(min_size=min_size, max_size=max_size, timeout=timeout)


def close_engine_pool() -> None:
    global _engine_pool
    with _engine_pool_lock:
        pool = _engine_pool
        _engine_pool = None
    if pool is not None:
        pool.close()


@contextmanager
def engine_connection() -> Iterator[Connection]:
    """Borrow a pooled connection to the Seymour Pool Engine database."""
    with get_engine_pool().connection() as connection:
        yield connection


@contextmanager
def miningcore_connection() -> Iterator[Connection]:
    """Open a read-oriented connection to the MiningCore database."""
    settings = get_settings()
    if not settings.miningcore_database_url:
        raise RuntimeError("SEYMOUR_MININGCORE_DATABASE_URL is not configured")
    with psycopg.connect(
        settings.miningcore_database_url,
        row_factory=dict_row,
        connect_timeout=5,
    ) as connection:
        yield connection


def test_engine_database() -> dict:
    try:
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT current_database() AS database_name,
                           current_user AS database_user,
                           version() AS server_version
                    """
                )
                row = cursor.fetchone()
        return {
            "status": "online",
            "summary": "Engine database connection succeeded",
            "details": row,
        }
    except Exception as exc:
        return {
            "status": "offline",
            "summary": "Engine database connection failed",
            "details": {"error": str(exc)},
        }


def test_miningcore_database() -> dict:
    settings = get_settings()
    if not settings.miningcore_database_url:
        return {
            "status": "disabled",
            "summary": "MiningCore database connection is not configured",
            "details": {},
        }
    try:
        with miningcore_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT current_database() AS database_name,
                           current_user AS database_user
                    """
                )
                row = cursor.fetchone()
        return {
            "status": "online",
            "summary": "MiningCore database connection succeeded",
            "details": row,
        }
    except Exception as exc:
        return {
            "status": "offline",
            "summary": "MiningCore database connection failed",
            "details": {"error": str(exc)},
        }
