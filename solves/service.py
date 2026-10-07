"""Business rules for sessions and solves."""
from . import repository

VALID_PENALTIES = ("OK", "+2", "DNF")


class ValidationError(ValueError):
    """The caller sent invalid data."""


class NotFoundError(LookupError):
    """The requested session or solve does not exist."""


def effective_time_ms(time_ms, penalty):
    """Time that counts for averages: +2 adds 2000 ms, DNF has no time."""
    if penalty == "DNF":
        return None
    if penalty == "+2":
        return time_ms + 2000
    return time_ms


def _check_penalty(penalty):
    if penalty not in VALID_PENALTIES:
        raise ValidationError(f"penalty must be one of {VALID_PENALTIES}")


def _with_effective(solve):
    solve["effective_time_ms"] = effective_time_ms(solve["time_ms"], solve["penalty"])
    return solve


def create_session(conn, name):
    name = (name or "").strip()
    if not name:
        raise ValidationError("session name is required")
    session_id = repository.create_session(conn, name)
    return repository.get_session(conn, session_id)


def add_solve(conn, session_id, time_ms, scramble, penalty="OK"):
    if repository.get_session(conn, session_id) is None:
        raise NotFoundError(f"session {session_id} not found")
    if not isinstance(time_ms, int) or isinstance(time_ms, bool) or time_ms <= 0:
        raise ValidationError("time_ms must be a positive integer")
    if not scramble or not scramble.strip():
        raise ValidationError("scramble is required")
    _check_penalty(penalty)
    solve_id = repository.insert_solve(conn, session_id, time_ms, penalty, scramble.strip())
    return _with_effective(repository.get_solve(conn, solve_id))


def set_penalty(conn, solve_id, penalty):
    _check_penalty(penalty)
    if repository.update_penalty(conn, solve_id, penalty) == 0:
        raise NotFoundError(f"solve {solve_id} not found")
    return _with_effective(repository.get_solve(conn, solve_id))


def delete_solve(conn, solve_id):
    if repository.delete_solve(conn, solve_id) == 0:
        raise NotFoundError(f"solve {solve_id} not found")


def list_solves(conn, session_id):
    if repository.get_session(conn, session_id) is None:
        raise NotFoundError(f"session {session_id} not found")
    return [_with_effective(s) for s in repository.list_solves(conn, session_id)]


def get_times(conn, session_id):
    """The one function the stats domain may use.

    Returns effective times in ms, oldest first. A DNF is None.
    """
    return [s["effective_time_ms"] for s in list_solves(conn, session_id)]
