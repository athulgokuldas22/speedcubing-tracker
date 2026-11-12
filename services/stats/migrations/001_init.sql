-- 001: the personal_bests table, as it was in Assignment 1, in SQL Server syntax.
-- session_id is a plain number: sessions live in the solves database.
CREATE TABLE personal_bests (
    session_id INT NOT NULL,
    kind VARCHAR(10) NOT NULL CHECK (kind IN ('single', 'ao5', 'ao12', 'ao100')),
    time_ms INT NOT NULL CHECK (time_ms > 0),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    PRIMARY KEY (session_id, kind)
);
