"""Applies the .sql files in migrations/ in name order, each one exactly once."""
import re
from pathlib import Path

from app.db import connect_with_retry

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def split_batches(sql):
    """Split a file on lines that only say GO, like sqlcmd does.

    SQL Server checks a whole batch before running it, so a column added with
    ALTER TABLE can only be used in the next batch.
    """
    batches = re.split(r"^\s*GO\s*$", sql, flags=re.MULTILINE | re.IGNORECASE)
    return [batch for batch in batches if batch.strip()]


def run_migrations():
    conn = connect_with_retry()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "IF OBJECT_ID('schema_migrations', 'U') IS NULL "
            "CREATE TABLE schema_migrations ("
            "version VARCHAR(255) PRIMARY KEY, "
            "applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME())"
        )
        conn.commit()

        cursor.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in cursor.fetchall()}

        pending = [p for p in sorted(MIGRATIONS_DIR.glob("*.sql")) if p.name not in applied]
        for path in pending:
            # The file and its row in schema_migrations commit together, or not at all.
            for batch in split_batches(path.read_text()):
                cursor.execute(batch)
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
            conn.commit()
            print(f"applied migration {path.name}", flush=True)

        if not pending:
            print("migrations: nothing to apply", flush=True)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
