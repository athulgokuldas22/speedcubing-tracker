from stats import records


def test_best_single_ignores_dnf():
    assert records.best_single([12000, None, 9000, 15000]) == 9000


def test_best_single_none_when_empty_or_all_dnf():
    assert records.best_single([]) is None
    assert records.best_single([None, None]) is None


def test_best_average_needs_enough_solves():
    assert records.best_average([10000] * 4, 5) is None


def test_best_average_picks_best_window():
    times = [20000] * 5 + [10000] * 5
    assert records.best_average(times, 5) == 10000


def test_best_average_skips_dnf_windows():
    # window 0 has two DNFs (a DNF average); later windows are valid
    times = [None, None, 10000, 10000, 10000, 10000, 10000]
    assert records.best_average(times, 5) == 10000


def test_best_average_none_when_every_window_is_dnf():
    assert records.best_average([None] * 6, 5) is None


def test_compute_bests_only_includes_available_kinds():
    bests = records.compute_bests([10000, 11000, 12000, 13000, 14000])
    assert bests == {"single": 10000, "ao5": 12000}


def test_detect_new_pbs_first_time_everything_is_new():
    new = {"single": 10000, "ao5": 12000}
    assert records.detect_new_pbs({}, new) == {"single", "ao5"}


def test_detect_new_pbs_only_improvements():
    old = {"single": 10000, "ao5": 12000}
    new = {"single": 9000, "ao5": 12000}
    assert records.detect_new_pbs(old, new) == {"single"}


def test_detect_new_pbs_slower_is_not_a_pb():
    assert records.detect_new_pbs({"single": 9000}, {"single": 10000}) == set()
