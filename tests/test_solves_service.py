import pytest

from solves import service
from solves.service import NotFoundError, ValidationError

SCRAMBLE = "R U R' U'"


def make_session(conn):
    return service.create_session(conn, "Practice")


def test_create_session_strips_name(conn):
    session = service.create_session(conn, "  Practice  ")
    assert session["name"] == "Practice"


@pytest.mark.parametrize("bad_name", ["", "   ", None])
def test_create_session_rejects_empty_name(conn, bad_name):
    with pytest.raises(ValidationError):
        service.create_session(conn, bad_name)


def test_add_solve_stores_time_and_defaults_to_ok(conn):
    session = make_session(conn)
    solve = service.add_solve(conn, session["id"], 12340, SCRAMBLE)
    assert solve["penalty"] == "OK"
    assert solve["effective_time_ms"] == 12340


def test_add_solve_unknown_session(conn):
    with pytest.raises(NotFoundError):
        service.add_solve(conn, 999, 10000, SCRAMBLE)


@pytest.mark.parametrize("bad_time", [0, -5, 12.5, "10000", True])
def test_add_solve_rejects_bad_time(conn, bad_time):
    session = make_session(conn)
    with pytest.raises(ValidationError):
        service.add_solve(conn, session["id"], bad_time, SCRAMBLE)


def test_add_solve_rejects_bad_penalty_and_empty_scramble(conn):
    session = make_session(conn)
    with pytest.raises(ValidationError):
        service.add_solve(conn, session["id"], 10000, SCRAMBLE, penalty="+4")
    with pytest.raises(ValidationError):
        service.add_solve(conn, session["id"], 10000, "  ")


def test_effective_time_ms():
    assert service.effective_time_ms(10000, "OK") == 10000
    assert service.effective_time_ms(10000, "+2") == 12000
    assert service.effective_time_ms(10000, "DNF") is None


def test_set_penalty_changes_effective_time(conn):
    session = make_session(conn)
    solve = service.add_solve(conn, session["id"], 10000, SCRAMBLE)
    updated = service.set_penalty(conn, solve["id"], "+2")
    assert updated["effective_time_ms"] == 12000
    assert updated["time_ms"] == 10000


def test_set_penalty_unknown_solve_and_invalid_value(conn):
    with pytest.raises(NotFoundError):
        service.set_penalty(conn, 999, "DNF")
    session = make_session(conn)
    solve = service.add_solve(conn, session["id"], 10000, SCRAMBLE)
    with pytest.raises(ValidationError):
        service.set_penalty(conn, solve["id"], "bogus")


def test_delete_solve(conn):
    session = make_session(conn)
    solve = service.add_solve(conn, session["id"], 10000, SCRAMBLE)
    service.delete_solve(conn, solve["id"])
    assert service.list_solves(conn, session["id"]) == []
    with pytest.raises(NotFoundError):
        service.delete_solve(conn, solve["id"])


def test_get_times_orders_oldest_first_with_dnf_as_none(conn):
    session = make_session(conn)
    service.add_solve(conn, session["id"], 10000, SCRAMBLE)
    service.add_solve(conn, session["id"], 12000, SCRAMBLE, penalty="+2")
    service.add_solve(conn, session["id"], 9000, SCRAMBLE, penalty="DNF")
    assert service.get_times(conn, session["id"]) == [10000, 14000, None]


def test_list_solves_unknown_session(conn):
    with pytest.raises(NotFoundError):
        service.list_solves(conn, 999)
