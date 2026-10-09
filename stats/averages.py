"""WCA-style averages. Pure functions: no database, no Flask."""
import math

AVERAGE_SIZES = (5, 12, 100)


def trim_count(n):
    """How many solves are dropped from each end: 5% of n, rounded up."""
    return math.ceil(n * 0.05)


def average_of(times):
    """Average of a window of effective times in ms (None means DNF).

    Drops the best and worst `trim_count` solves and means the rest.
    Returns the result in ms rounded half up to a centisecond, or None
    if there are more DNFs than can be dropped.
    """
    n = len(times)
    if n < 5:
        raise ValueError("an average needs at least 5 times")
    trim = trim_count(n)
    dnf_count = sum(1 for t in times if t is None)
    if dnf_count > trim:
        return None
    # DNFs sort last, so they land in the slice that gets trimmed away.
    ordered = sorted(times, key=lambda t: math.inf if t is None else t)
    kept = ordered[trim:n - trim]
    total = sum(kept)
    count = len(kept)
    # Integer arithmetic for round-half-up to the nearest 10 ms (no float error).
    return ((2 * total + 10 * count) // (20 * count)) * 10
