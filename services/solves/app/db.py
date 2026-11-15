import os
import time
from urllib.parse import unquote, urlparse

import pymssql
from flask import g


def connect():
    """Open a connection from DATABASE_URL: mssql://user:password@host:port/database"""
    url = urlparse(os.environ["DATABASE_URL"])
    return pymssql.connect(
        server=url.hostname,
        port=str(url.port or 1433),
        user=unquote(url.username),
        password=unquote(url.password),
        database=url.path.lstrip("/"),
        login_timeout=5,
        timeout=5,
    )


def connect_with_retry(attempts=10, first_delay=1, max_delay=15):
    """Keep trying with exponential backoff: 1, 2, 4, 8, then 15 s between attempts.

    SQL Server in compose needs about 20 s to start, and a paused Azure SQL serverless
    database can take about a minute to resume (error 40613 until then).
    """
    delay = first_delay
    for attempt in range(1, attempts + 1):
        try:
            return connect()
        except pymssql.Error as error:
            if attempt == attempts:
                raise
            print(f"database not ready ({attempt}/{attempts}), retrying in {delay}s: {error}", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, max_delay)


def check_read_write():
    """True if this service can read and write its own database. It changes nothing."""
    try:
        conn = connect()
    except pymssql.Error:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM schema_migrations")
        cursor.fetchone()
        # Needs write permission on the table, matches no rows, and is rolled back anyway.
        cursor.execute("UPDATE schema_migrations SET applied_at = applied_at WHERE 1 = 0")
        conn.rollback()
        return True
    except pymssql.Error:
        return False
    finally:
        conn.close()


def get_db():
    """One connection per request, stored on flask.g."""
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(exc=None):
    """Registered as a teardown hook so the connection is always closed."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
