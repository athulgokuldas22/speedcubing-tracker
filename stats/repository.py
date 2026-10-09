"""SQL only for the personal_bests table."""


def get_pbs(conn, session_id):
    rows = conn.execute(
        "SELECT kind, time_ms FROM personal_bests WHERE session_id = ?",
        (session_id,),
    ).fetchall()
    return {row["kind"]: row["time_ms"] for row in rows}


def replace_pbs(conn, session_id, pbs):
    """Replace a session's stored personal bests in one transaction."""
    conn.execute("DELETE FROM personal_bests WHERE session_id = ?", (session_id,))
    conn.executemany(
        "INSERT INTO personal_bests (session_id, kind, time_ms) VALUES (?, ?, ?)",
        [(session_id, kind, value) for kind, value in pbs.items()],
    )
    conn.commit()
