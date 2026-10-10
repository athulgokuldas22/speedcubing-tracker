import pytest

import config
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "api.db"))
    return create_app().test_client()


def make_session(client):
    return client.post("/api/sessions", json={"name": "Practice"}).get_json()


def add_solve(client, session_id, time_ms=10000, **extra):
    body = {"time_ms": time_ms, "scramble": "R U R' U'", **extra}
    return client.post(f"/api/sessions/{session_id}/solves", json=body)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_scramble_endpoint_returns_20_moves(client):
    scramble = client.get("/api/scramble").get_json()["scramble"]
    assert len(scramble.split()) == 20


def test_create_and_list_sessions(client):
    session = make_session(client)
    listed = client.get("/api/sessions").get_json()
    assert [s["id"] for s in listed] == [session["id"]]


def test_empty_session_name_is_400(client):
    response = client.post("/api/sessions", json={"name": ""})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_solve_lifecycle_add_penalty_delete(client):
    session = make_session(client)
    created = add_solve(client, session["id"])
    assert created.status_code == 201
    solve_id = created.get_json()["id"]

    patched = client.patch(f"/api/solves/{solve_id}", json={"penalty": "+2"})
    assert patched.get_json()["effective_time_ms"] == 12000

    assert client.delete(f"/api/solves/{solve_id}").status_code == 204
    assert client.get(f"/api/sessions/{session['id']}/solves").get_json() == []


def test_unknown_session_is_404(client):
    assert add_solve(client, 999).status_code == 404


def test_stats_reports_new_pbs_only_once(client):
    session = make_session(client)
    for t in (10000, 11000, 12000, 13000, 14000):
        add_solve(client, session["id"], t)
    first = client.get(f"/api/sessions/{session['id']}/stats").get_json()
    assert first["solve_count"] == 5
    assert first["current"] == {"ao5": 12000}
    assert first["new_pbs"] == ["ao5", "single"]
    second = client.get(f"/api/sessions/{session['id']}/stats").get_json()
    assert second["new_pbs"] == []


def test_stats_unknown_session_is_404(client):
    assert client.get("/api/sessions/999/stats").status_code == 404
