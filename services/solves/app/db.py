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


def connect_with_retry(attempts=30, delay=2):
    """SQL Server needs about 20 s to start, so try again a few times before giving up."""
    for attempt in range(1, attempts + 1):
        try:
            return connect()
        except pymssql.Error as error:
            if attempt == attempts:
                raise
            print(f"database not ready ({attempt}/{attempts}): {error}", flush=True)
            time.sleep(delay)


def init_db(statements):
    """Run each schema statement. They check first, so this is safe on every startup."""
    conn = connect_with_retry()
    try:
        cursor = conn.cursor()
        for statement in statements:
            cursor.execute(statement)
        conn.commit()
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
