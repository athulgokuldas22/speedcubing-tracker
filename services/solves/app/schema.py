# Each statement checks before creating, so running them on every startup is safe.
SCHEMA = [
    """
    IF OBJECT_ID('sessions', 'U') IS NULL
    CREATE TABLE sessions (
        id INT IDENTITY PRIMARY KEY,
        name NVARCHAR(MAX) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    )
    """,
    """
    IF OBJECT_ID('solves', 'U') IS NULL
    CREATE TABLE solves (
        id INT IDENTITY PRIMARY KEY,
        session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        time_ms INT NOT NULL CHECK (time_ms > 0),
        penalty VARCHAR(3) NOT NULL DEFAULT 'OK' CHECK (penalty IN ('OK', '+2', 'DNF')),
        scramble NVARCHAR(MAX) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    )
    """,
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_solves_session')
    CREATE INDEX idx_solves_session ON solves (session_id, id)
    """,
]
