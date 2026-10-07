"""SQL only. No business rules live here."""


def create_session(conn, name):
    cur = conn.execute("INSERT INTO sessions (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def get_session(conn, session_id):
    row = conn.execute(
        "SELECT id, name, created_at FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    return dict(row) if row else None


def list_sessions(conn):
    rows = conn.execute(
        "SELECT id, name, created_at FROM sessions ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def insert_solve(conn, session_id, time_ms, penalty, scramble):
    cur = conn.execute(
        "INSERT INTO solves (session_id, time_ms, penalty, scramble) "
        "VALUES (?, ?, ?, ?)",
        (session_id, time_ms, penalty, scramble),
    )
    conn.commit()
    return cur.lastrowid


def get_solve(conn, solve_id):
    row = conn.execute(
        "SELECT id, session_id, time_ms, penalty, scramble, created_at "
        "FROM solves WHERE id = ?",
        (solve_id,),
    ).fetchone()
    return dict(row) if row else None


def list_solves(conn, session_id):
    rows = conn.execute(
        "SELECT id, session_id, time_ms, penalty, scramble, created_at "
        "FROM solves WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_penalty(conn, solve_id, penalty):
    cur = conn.execute(
        "UPDATE solves SET penalty = ? WHERE id = ?", (penalty, solve_id)
    )
    conn.commit()
    return cur.rowcount


def delete_solve(conn, solve_id):
    cur = conn.execute("DELETE FROM solves WHERE id = ?", (solve_id,))
    conn.commit()
    return cur.rowcount
