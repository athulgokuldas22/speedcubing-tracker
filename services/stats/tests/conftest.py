"""Database fixtures for the tests that need a real SQL Server.

CI starts a throwaway SQL Server and sets TEST_DATABASE_URL to its master database.
Without it the database tests are skipped locally, but in CI they must run.
"""
import os
from urllib.parse import urlparse

import pytest

from app import db, main, migrate

TEST_DB = "speedcubing_test"
TABLES = ["personal_bests"]


@pytest.fixture(scope="session")
def database():
    server_url = os.environ.get("TEST_DATABASE_URL")
    if not server_url:
        if os.environ.get("CI"):
            pytest.fail("TEST_DATABASE_URL must be set in CI")
        pytest.skip("TEST_DATABASE_URL is not set, so there is no SQL Server to test against")

    os.environ["DATABASE_URL"] = server_url
    conn = db.connect_with_retry()
    conn.autocommit(True)  # CREATE DATABASE cannot run inside a transaction
    conn.cursor().execute(f"IF DB_ID('{TEST_DB}') IS NULL CREATE DATABASE {TEST_DB}")
    conn.close()

    os.environ["DATABASE_URL"] = urlparse(server_url)._replace(path=f"/{TEST_DB}").geturl()
    migrate.run_migrations()


@pytest.fixture
def conn(database):
    """A connection to the test database, emptied before each test."""
    connection = db.connect()
    cursor = connection.cursor()
    for table in TABLES:
        cursor.execute(f"DELETE FROM {table}")
    connection.commit()
    yield connection
    connection.close()


@pytest.fixture
def api(conn):
    """The real Flask app, talking to the test database."""
    return main.create_app().test_client()
