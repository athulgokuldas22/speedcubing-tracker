import pytest

from app import service
from app.solves_client import NotFoundError


@pytest.fixture
def times(monkeypatch):
    """Stands in for the solves service: session id -> list of effective times."""
    sessions = {}

    def fake_get_times(session_id):
        if session_id not in sessions:
            raise NotFoundError(f"session {session_id} not found")
        return list(sessions[session_id])

    monkeypatch.setattr(service, "get_times", fake_get_times)
    return sessions


def test_refresh_pbs_first_time(conn, times):
    times[1] = [10000, 11000, 12000, 13000, 14000]
    result = service.refresh_pbs(conn, 1)
    assert result["personal_bests"] == {"single": 10000, "ao5": 12000}
    assert result["new"] == ["ao5", "single"]


def test_refresh_pbs_reports_only_improvements(conn, times):
    times[1] = [10000, 11000, 12000, 13000, 14000]
    service.refresh_pbs(conn, 1)
    times[1].append(9000)
    result = service.refresh_pbs(conn, 1)
    assert result["new"] == ["single"]
    assert result["personal_bests"]["single"] == 9000


def test_refresh_pbs_corrects_stored_bests_after_a_solve_is_deleted(conn, times):
    times[1] = [10000, 11000, 12000, 13000, 14000]
    service.refresh_pbs(conn, 1)
    times[1].pop(0)
    service.refresh_pbs(conn, 1)
    assert service.get_summary(conn, 1)["personal_bests"] == {"single": 11000}


def test_refresh_pbs_with_no_solves_stores_nothing(conn, times):
    times[1] = []
    assert service.refresh_pbs(conn, 1) == {"personal_bests": {}, "new": []}


def test_summary_only_has_averages_with_enough_solves(conn, times):
    times[1] = [10000, 11000, 12000, 13000, 14000]
    summary = service.get_summary(conn, 1)
    assert summary["solve_count"] == 5
    assert summary["current"] == {"ao5": 12000}


def test_summary_marks_dnf_average_as_none(conn, times):
    times[1] = [None, None, 12000, 13000, 14000]
    assert service.get_summary(conn, 1)["current"] == {"ao5": None}


def test_unknown_session_raises_not_found(conn, times):
    with pytest.raises(NotFoundError):
        service.get_summary(conn, 999)
    with pytest.raises(NotFoundError):
        service.refresh_pbs(conn, 999)
