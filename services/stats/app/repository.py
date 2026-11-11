"""SQL only for the personal_bests table."""


def get_pbs(conn, session_id):
    cursor = conn.cursor(as_dict=True)
    cursor.execute(
        "SELECT kind, time_ms FROM personal_bests WHERE session_id = %s", (session_id,)
    )
    return {row["kind"]: row["time_ms"] for row in cursor.fetchall()}


def replace_pbs(conn, session_id, pbs):
    """Replace a session's stored personal bests in one transaction."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM personal_bests WHERE session_id = %s", (session_id,))
    cursor.executemany(
        "INSERT INTO personal_bests (session_id, kind, time_ms) VALUES (%s, %s, %s)",
        [(session_id, kind, value) for kind, value in pbs.items()],
    )
    conn.commit()
