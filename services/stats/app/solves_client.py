"""The seam: stats gets solve data only through this HTTP call to the solves service."""
import os

import requests


class NotFoundError(LookupError):
    """The session does not exist in the solves service."""


class SolvesUnavailable(Exception):
    """The solves service did not answer, or answered with an error."""


def get_times(session_id):
    """Effective times in ms, oldest first. A DNF is None."""
    url = f"{os.environ['SOLVES_URL']}/api/sessions/{session_id}/times"
    try:
        response = requests.get(url, timeout=2)
    except requests.RequestException:
        raise SolvesUnavailable("solves service unavailable, try again later")
    if response.status_code == 404:
        raise NotFoundError(f"session {session_id} not found")
    if response.status_code != 200:
        raise SolvesUnavailable("solves service unavailable, try again later")
    return response.json()["times"]
