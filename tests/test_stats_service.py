import pytest

from solves import service as solves_service
from stats import service

SCRAMBLE = "R U R' U'"


def make_session_with(conn, times):
    session = solves_service.create_session(conn, "Practice")
    ids = [
        solves_service.add_solve(conn, session["id"], t, SCRAMBLE)["id"]
        for t in times
    ]
    return session["id"], ids


def test_refresh_pbs_first_time(conn):
    session_id, _ = make_session_with(conn, [10000, 11000, 12000, 13000, 14000])
    result = service.refresh_pbs(conn, session_id)
    assert result["personal_bests"] == {"single": 10000, "ao5": 12000}
    assert result["new"] == ["ao5", "single"]


def test_refresh_pbs_reports_only_improvements(conn):
    session_id, _ = make_session_with(conn, [10000, 11000, 12000, 13000, 14000])
    service.refresh_pbs(conn, session_id)
    solves_service.add_solve(conn, session_id, 9000, SCRAMBLE)
    result = service.refresh_pbs(conn, session_id)
    assert result["new"] == ["single"]
    assert result["personal_bests"]["single"] == 9000


def test_refresh_pbs_corrects_stored_bests_after_delete(conn):
    session_id, ids = make_session_with(conn, [10000, 11000, 12000, 13000, 14000])
    service.refresh_pbs(conn, session_id)
    solves_service.delete_solve(conn, ids[0])
    service.refresh_pbs(conn, session_id)
    assert service.get_summary(conn, session_id)["personal_bests"] == {"single": 11000}


def test_summary_only_has_averages_with_enough_solves(conn):
    session_id, _ = make_session_with(conn, [10000, 11000, 12000, 13000, 14000])
    summary = service.get_summary(conn, session_id)
    assert summary["solve_count"] == 5
    assert summary["current"] == {"ao5": 12000}


def test_summary_marks_dnf_average_as_none(conn):
    session_id, ids = make_session_with(conn, [10000, 11000, 12000, 13000, 14000])
    solves_service.set_penalty(conn, ids[0], "DNF")
    solves_service.set_penalty(conn, ids[1], "DNF")
    assert service.get_summary(conn, session_id)["current"] == {"ao5": None}


def test_unknown_session_raises_lookup_error(conn):
    with pytest.raises(LookupError):
        service.get_summary(conn, 999)
    with pytest.raises(LookupError):
        service.refresh_pbs(conn, 999)
