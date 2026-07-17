from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from seymour_pool_engine.config import get_settings


@contextmanager
def engine_connection() -> Iterator[Connection]:
    """Open a connection to the Seymour Pool Engine database."""

    settings = get_settings()

    with psycopg.connect(
        settings.engine_database_url,
        row_factory=dict_row,
        connect_timeout=5,
    ) as connection:
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
                    SELECT
                        current_database() AS database_name,
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
                    SELECT
                        current_database() AS database_name,
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
