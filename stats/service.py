"""Stats use case: solve data comes only through solves.get_times."""
from solves import get_times

from . import averages, records, repository


def get_summary(conn, session_id):
    """Read-only view: current averages and the stored personal bests.

    A missing key in `current` means too few solves; None means a DNF average.
    """
    times = get_times(conn, session_id)
    current = {}
    for n in averages.AVERAGE_SIZES:
        if len(times) >= n:
            current[f"ao{n}"] = averages.average_of(times[-n:])
    return {
        "solve_count": len(times),
        "current": current,
        "personal_bests": repository.get_pbs(conn, session_id),
    }


def refresh_pbs(conn, session_id):
    """Recompute personal bests from the solves and store them.

    Recomputing (rather than only comparing the newest solve) keeps stored
    bests correct after a solve is deleted or its penalty changes.
    """
    times = get_times(conn, session_id)
    old = repository.get_pbs(conn, session_id)
    current = records.compute_bests(times)
    new = records.detect_new_pbs(old, current)
    repository.replace_pbs(conn, session_id, current)
    return {"personal_bests": current, "new": sorted(new)}
