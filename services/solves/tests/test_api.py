def make_session(api):
    return api.post("/api/sessions", json={"name": "Practice"}).get_json()


def add_solve(api, session_id, time_ms=10000, **extra):
    body = {"time_ms": time_ms, "scramble": "R U R' U'", **extra}
    return api.post(f"/api/sessions/{session_id}/solves", json=body)


def test_scramble_endpoint_returns_20_moves(api):
    scramble = api.get("/api/scramble").get_json()["scramble"]
    assert len(scramble.split()) == 20


def test_create_and_list_sessions(api):
    session = make_session(api)
    listed = api.get("/api/sessions").get_json()
    assert [s["id"] for s in listed] == [session["id"]]


def test_empty_session_name_is_400(api):
    response = api.post("/api/sessions", json={"name": ""})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_solve_lifecycle_add_penalty_delete(api):
    session = make_session(api)
    created = add_solve(api, session["id"])
    assert created.status_code == 201
    solve_id = created.get_json()["id"]

    patched = api.patch(f"/api/solves/{solve_id}", json={"penalty": "+2"})
    assert patched.get_json()["effective_time_ms"] == 12000

    assert api.delete(f"/api/solves/{solve_id}").status_code == 204
    assert api.get(f"/api/sessions/{session['id']}/solves").get_json() == []


def test_unknown_session_is_404(api):
    assert add_solve(api, 999).status_code == 404


def test_times_endpoint_matches_what_stats_expects(api):
    """The solves side of the seam: stats reads exactly this shape."""
    session = make_session(api)
    add_solve(api, session["id"], 10000)
    add_solve(api, session["id"], 12000, penalty="+2")
    add_solve(api, session["id"], 9000, penalty="DNF")
    response = api.get(f"/api/sessions/{session['id']}/times")
    assert response.status_code == 200
    assert response.get_json() == {"times": [10000, 14000, None]}
    assert api.get("/api/sessions/999/times").status_code == 404


def test_health_is_200_against_a_real_database(api):
    assert api.get("/health").get_json()["db"] == "ok"
