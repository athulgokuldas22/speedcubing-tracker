"""Integration test across the seam.

The real stats app (routes, service, client, repository and SQL Server) calls a stub of
the solves service over real HTTP. The stub answers in the same shape that
test_times_endpoint_matches_what_stats_expects checks on the solves side (ADR-9).
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

SESSIONS = {1: [10000, 11000, 12000, 13000, 14000]}


class FakeSolves(BaseHTTPRequestHandler):
    def do_GET(self):
        parts = self.path.strip("/").split("/")  # api / sessions / <id> / times
        session_id = int(parts[2])
        if session_id == 500:
            self.reply(500, {"error": "solves database is down"})
        elif session_id in SESSIONS:
            self.reply(200, {"times": SESSIONS[session_id]})
        else:
            self.reply(404, {"error": f"session {session_id} not found"})

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def solves_url(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), FakeSolves)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("SOLVES_URL", url)
    yield server
    server.shutdown()
    server.server_close()


def test_stats_flow_gets_times_from_solves_over_http(api, solves_url):
    first = api.get("/api/sessions/1/stats").get_json()
    assert first["solve_count"] == 5
    assert first["current"] == {"ao5": 12000}
    assert first["new_pbs"] == ["ao5", "single"]
    second = api.get("/api/sessions/1/stats").get_json()
    assert second["new_pbs"] == []


def test_unknown_session_in_solves_is_404_in_stats(api, solves_url):
    assert api.get("/api/sessions/7/stats").status_code == 404


def test_solves_error_becomes_a_clear_503(api, solves_url):
    response = api.get("/api/sessions/500/stats")
    assert response.status_code == 503
    assert response.get_json() == {"error": "solves service unavailable, try again later"}


def test_solves_stopped_gives_503_quickly_not_a_hang(api, solves_url):
    solves_url.shutdown()
    solves_url.server_close()
    started = time.perf_counter()
    response = api.get("/api/sessions/1/stats")
    assert response.status_code == 503
    assert time.perf_counter() - started < 3  # the client timeout is 2 s
