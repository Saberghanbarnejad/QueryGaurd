import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
import pytest
from psycopg import Connection


def database_tests_enabled() -> bool:
    return os.getenv("QUERYGUARD_RUN_DB_TESTS") == "1"


DATABASE_TEST_MARK = pytest.mark.skipif(
    not database_tests_enabled(),
    reason="set QUERYGUARD_RUN_DB_TESTS=1 to run PostgreSQL database tests",
)


@contextmanager
def connect_as(username: str, password_variable: str) -> Iterator[Connection[Any]]:
    password = os.environ.get(password_variable)
    if not password:
        pytest.fail(f"{password_variable} must be set for PostgreSQL database tests")

    connection = psycopg.connect(
        host="127.0.0.1",
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "queryguard"),
        user=username,
        password=password,
        autocommit=True,
    )
    try:
        yield connection
    finally:
        connection.close()
