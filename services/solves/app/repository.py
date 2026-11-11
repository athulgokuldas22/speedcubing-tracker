"""SQL only. No business rules live here."""


def create_session(conn, name):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (name) OUTPUT INSERTED.id VALUES (%s)", (name,))
    session_id = cursor.fetchone()[0]
    conn.commit()
    return session_id


def get_session(conn, session_id):
    cursor = conn.cursor(as_dict=True)
    cursor.execute(
        "SELECT id, name, CONVERT(VARCHAR(19), created_at, 120) AS created_at "
        "FROM sessions WHERE id = %s",
        (session_id,),
    )
    return cursor.fetchone()


def list_sessions(conn):
    cursor = conn.cursor(as_dict=True)
    cursor.execute(
        "SELECT id, name, CONVERT(VARCHAR(19), created_at, 120) AS created_at "
        "FROM sessions ORDER BY id"
    )
    return cursor.fetchall()


def insert_solve(conn, session_id, time_ms, penalty, scramble):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO solves (session_id, time_ms, penalty, scramble) "
        "OUTPUT INSERTED.id VALUES (%s, %s, %s, %s)",
        (session_id, time_ms, penalty, scramble),
    )
    solve_id = cursor.fetchone()[0]
    conn.commit()
    return solve_id


def get_solve(conn, solve_id):
    cursor = conn.cursor(as_dict=True)
    cursor.execute(
        "SELECT id, session_id, time_ms, penalty, scramble, "
        "CONVERT(VARCHAR(19), created_at, 120) AS created_at "
        "FROM solves WHERE id = %s",
        (solve_id,),
    )
    return cursor.fetchone()


def list_solves(conn, session_id):
    cursor = conn.cursor(as_dict=True)
    cursor.execute(
        "SELECT id, session_id, time_ms, penalty, scramble, "
        "CONVERT(VARCHAR(19), created_at, 120) AS created_at "
        "FROM solves WHERE session_id = %s ORDER BY id",
        (session_id,),
    )
    return cursor.fetchall()


def update_penalty(conn, solve_id, penalty):
    cursor = conn.cursor()
    cursor.execute("UPDATE solves SET penalty = %s WHERE id = %s", (penalty, solve_id))
    count = cursor.rowcount
    conn.commit()
    return count


def delete_solve(conn, solve_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM solves WHERE id = %s", (solve_id,))
    count = cursor.rowcount
    conn.commit()
    return count
