# Database schema

```mermaid
erDiagram
    SESSIONS ||--o{ SOLVES : "contains (FK, ON DELETE CASCADE)"
    SESSIONS ||..o{ PERSONAL_BESTS : "logical reference only (no FK)"

    SESSIONS {
        INTEGER id PK
        TEXT name
        TEXT created_at
    }
    SOLVES {
        INTEGER id PK
        INTEGER session_id FK
        INTEGER time_ms
        TEXT penalty "OK, +2 or DNF"
        TEXT scramble
        TEXT created_at
    }
    PERSONAL_BESTS {
        INTEGER session_id PK
        TEXT kind PK "single, ao5, ao12 or ao100"
        INTEGER time_ms
        TEXT updated_at
    }
```

Domain ownership: `sessions` and `solves` belong to the solves domain, `personal_bests` to the stats domain. The dotted line is a convention kept in code, not a database constraint.
