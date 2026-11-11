import pytest

from app import solves_client


def test_get_times_raises_unavailable_when_solves_is_down(monkeypatch):
    # Nothing listens on port 1, so the call fails like a stopped solves service.
    monkeypatch.setenv("SOLVES_URL", "http://127.0.0.1:1")
    with pytest.raises(solves_client.SolvesUnavailable):
        solves_client.get_times(1)
