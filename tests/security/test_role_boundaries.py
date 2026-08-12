import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
import pytest
from psycopg import Connection, errors, sql


def _database_tests_enabled() -> bool:
    return os.getenv("QUERYGUARD_RUN_DB_TESTS") == "1"


pytestmark = pytest.mark.skipif(
    not _database_tests_enabled(),
    reason="set QUERYGUARD_RUN_DB_TESTS=1 to run PostgreSQL security tests",
)


@contextmanager
def _connect(username: str, password_variable: str) -> Iterator[Connection[Any]]:
    password = os.environ.get(password_variable)
    if not password:
        pytest.fail(f"{password_variable} must be set for database security tests")

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


def test_application_roles_are_unprivileged_login_roles() -> None:
    expected_limits = {
        "queryguard_owner": 2,
        "queryguard_runtime": 10,
        "queryguard_audit": 5,
    }
    with _connect(os.getenv("POSTGRES_USER", "queryguard_bootstrap"), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolcanlogin,
                   rolreplication, rolbypassrls, rolconnlimit
            FROM pg_catalog.pg_roles
            WHERE rolname = ANY(%s)
            """,
            (list(expected_limits),),
        ).fetchall()

    assert len(rows) == 3
    for row in rows:
        (
            role_name,
            is_superuser,
            can_create_db,
            can_create_role,
            can_login,
            can_replicate,
            can_bypass_rls,
            limit,
        ) = row
        assert role_name in expected_limits
        assert is_superuser is False
        assert can_create_db is False
        assert can_create_role is False
        assert can_login is True
        assert can_replicate is False
        assert can_bypass_rls is False
        assert limit == expected_limits[role_name]


def test_schema_access_is_separated() -> None:
    with _connect(os.getenv("POSTGRES_USER", "queryguard_bootstrap"), "POSTGRES_PASSWORD") as conn:
        permissions = conn.execute(
            """
            SELECT
                has_schema_privilege('queryguard_runtime', 'erp', 'USAGE'),
                has_schema_privilege('queryguard_runtime', 'erp', 'CREATE'),
                has_schema_privilege('queryguard_runtime', 'audit', 'USAGE'),
                has_schema_privilege('queryguard_audit', 'audit', 'USAGE'),
                has_schema_privilege('queryguard_audit', 'audit', 'CREATE'),
                has_schema_privilege('queryguard_audit', 'erp', 'USAGE'),
                has_database_privilege('queryguard_runtime', current_database(), 'TEMP'),
                has_database_privilege('queryguard_audit', current_database(), 'TEMP')
            """
        ).fetchone()

    assert permissions == (True, False, False, True, False, False, False, False)


def test_owner_owns_only_the_application_schemas() -> None:
    with _connect(os.getenv("POSTGRES_USER", "queryguard_bootstrap"), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT nspname, pg_catalog.pg_get_userbyid(nspowner)
            FROM pg_catalog.pg_namespace
            WHERE nspname = ANY(%s)
            ORDER BY nspname
            """,
            (["audit", "erp"],),
        ).fetchall()

    assert rows == [("audit", "queryguard_owner"), ("erp", "queryguard_owner")]


@pytest.mark.parametrize("target_schema", ["erp", "audit", "public"])
def test_runtime_cannot_create_objects_even_after_disabling_read_only_default(
    target_schema: str,
) -> None:
    with _connect("queryguard_runtime", "QUERYGUARD_RUNTIME_PASSWORD") as conn:
        conn.execute("SET default_transaction_read_only = off")
        conn.execute("BEGIN")
        try:
            with pytest.raises(errors.InsufficientPrivilege):
                conn.execute(
                    sql.SQL("CREATE TABLE {}.queryguard_permission_probe (id integer)").format(
                        sql.Identifier(target_schema)
                    )
                )
        finally:
            conn.execute("ROLLBACK")


@pytest.mark.parametrize("target_schema", ["erp", "audit", "public"])
def test_audit_role_cannot_create_objects(target_schema: str) -> None:
    with _connect("queryguard_audit", "QUERYGUARD_AUDIT_PASSWORD") as conn:
        conn.execute("BEGIN")
        try:
            with pytest.raises(errors.InsufficientPrivilege):
                conn.execute(
                    sql.SQL("CREATE TABLE {}.queryguard_permission_probe (id integer)").format(
                        sql.Identifier(target_schema)
                    )
                )
        finally:
            conn.execute("ROLLBACK")


def test_runtime_session_has_defensive_defaults() -> None:
    with _connect("queryguard_runtime", "QUERYGUARD_RUNTIME_PASSWORD") as conn:
        settings = conn.execute(
            """
            SELECT current_user,
                   current_setting('default_transaction_read_only'),
                   current_setting('statement_timeout'),
                   current_setting('search_path')
            """
        ).fetchone()

    assert settings is not None
    current_user, read_only, statement_timeout, search_path = settings
    assert current_user == "queryguard_runtime"
    assert read_only == "on"
    assert statement_timeout == "5s"
    assert search_path == "pg_catalog, erp"
