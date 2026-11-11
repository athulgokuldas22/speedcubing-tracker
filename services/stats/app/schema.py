# Checks before creating, so running it on every startup is safe.
SCHEMA = [
    """
    IF OBJECT_ID('personal_bests', 'U') IS NULL
    CREATE TABLE personal_bests (
        session_id INT NOT NULL,
        kind VARCHAR(10) NOT NULL CHECK (kind IN ('single', 'ao5', 'ao12', 'ao100')),
        time_ms INT NOT NULL CHECK (time_ms > 0),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        PRIMARY KEY (session_id, kind)
    )
    """,
]
