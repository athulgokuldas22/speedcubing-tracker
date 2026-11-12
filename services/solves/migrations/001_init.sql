-- 001: the solves tables, as they were in Assignment 1, in SQL Server syntax.
CREATE TABLE sessions (
    id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE solves (
    id INT IDENTITY PRIMARY KEY,
    session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    time_ms INT NOT NULL CHECK (time_ms > 0),
    penalty VARCHAR(3) NOT NULL DEFAULT 'OK' CHECK (penalty IN ('OK', '+2', 'DNF')),
    scramble NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX idx_solves_session ON solves (session_id, id);
