SCHEMA = """
CREATE TABLE IF NOT EXISTS personal_bests (
    session_id INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('single', 'ao5', 'ao12', 'ao100')),
    time_ms INTEGER NOT NULL CHECK (time_ms > 0),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (session_id, kind)
);
"""
