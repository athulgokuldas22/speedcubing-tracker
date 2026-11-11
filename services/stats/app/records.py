"""Personal best logic. Pure functions: no database, no Flask."""
from . import averages


def best_single(times):
    valid = [t for t in times if t is not None]
    return min(valid) if valid else None


def best_average(times, n):
    """Best average of n over every window of n consecutive solves."""
    if len(times) < n:
        return None
    results = [
        averages.average_of(times[i:i + n]) for i in range(len(times) - n + 1)
    ]
    valid = [r for r in results if r is not None]
    return min(valid) if valid else None


def compute_bests(times):
    """Best single and best ao5/ao12/ao100, leaving out kinds with no value."""
    bests = {"single": best_single(times)}
    for n in averages.AVERAGE_SIZES:
        bests[f"ao{n}"] = best_average(times, n)
    return {kind: value for kind, value in bests.items() if value is not None}


def detect_new_pbs(old, new):
    """Kinds where `new` beats `old` (or has no old value). Lower is better."""
    return {
        kind for kind, value in new.items()
        if kind not in old or value < old[kind]
    }
