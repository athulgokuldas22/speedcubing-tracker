import pymssql
import pytest

from app import db, main


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "run_migrations", lambda: None)
    return main.create_app().test_client()


def test_health_is_200_with_version_when_db_reads_and_writes(client, monkeypatch):
    monkeypatch.setattr(db, "check_read_write", lambda: True)
    monkeypatch.setenv("GIT_SHA", "abc123")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "db": "ok", "version": "abc123"}


def test_health_is_503_when_db_is_down(client, monkeypatch):
    monkeypatch.setattr(db, "check_read_write", lambda: False)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.get_json()["db"] == "error"


def test_every_request_logs_method_path_status_and_duration(client, monkeypatch, capsys):
    monkeypatch.setattr(db, "check_read_write", lambda: True)
    client.get("/health")
    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert line.startswith("GET /health 200 ")
    assert line.endswith("ms")


def test_connect_with_retry_backs_off_then_succeeds(monkeypatch):
    attempts = []
    sleeps = []

    def fake_connect():
        attempts.append(1)
        if len(attempts) < 4:
            raise pymssql.OperationalError("40613 database is not currently available")
        return "connection"

    monkeypatch.setattr(db, "connect", fake_connect)
    monkeypatch.setattr(db.time, "sleep", sleeps.append)
    assert db.connect_with_retry() == "connection"
    assert sleeps == [1, 2, 4]


def test_connect_with_retry_gives_up_after_the_last_attempt(monkeypatch):
    def always_fails():
        raise pymssql.OperationalError("down")

    monkeypatch.setattr(db, "connect", always_fails)
    monkeypatch.setattr(db.time, "sleep", lambda seconds: None)
    with pytest.raises(pymssql.OperationalError):
        db.connect_with_retry(attempts=3)


def test_check_read_write_is_false_when_it_cannot_connect(monkeypatch):
    def always_fails():
        raise pymssql.OperationalError("down")

    monkeypatch.setattr(db, "connect", always_fails)
    assert db.check_read_write() is False
