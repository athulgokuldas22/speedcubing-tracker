import os
import sqlite3

from flask import g

import config


def get_connection(db_path=None):
    """Open a SQLite connection; rows can be read like dicts."""
    conn = sqlite3.connect(db_path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(schemas=(), db_path=None):
    """Create the data directory and run each domain's schema script.

    Safe to call on every startup (schemas use CREATE TABLE IF NOT EXISTS),
    so no manual migration step is needed.
    """
    if db_path is None:
        os.makedirs(config.DATA_DIR, exist_ok=True)
    conn = get_connection(db_path)
    try:
        for schema in schemas:
            conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def get_db():
    """One connection per request, stored on flask.g."""
    if "db" not in g:
        g.db = get_connection()
    return g.db


def close_db(exc=None):
    """Registered as a teardown hook so the connection is always closed."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
