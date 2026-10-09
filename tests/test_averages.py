import pytest

from stats import averages


def test_trim_count():
    assert averages.trim_count(5) == 1
    assert averages.trim_count(12) == 1
    assert averages.trim_count(100) == 5


def test_ao5_drops_best_and_worst():
    assert averages.average_of([10000, 11000, 12000, 13000, 14000]) == 12000


def test_order_does_not_matter():
    assert averages.average_of([14000, 10000, 13000, 11000, 12000]) == 12000


def test_ao5_one_dnf_is_dropped_as_worst():
    # sorted: 10000, 11000, 13000, 14000, DNF -> keeps 11000, 13000, 14000
    assert averages.average_of([10000, 11000, None, 13000, 14000]) == 12670


def test_ao5_two_dnfs_is_dnf():
    assert averages.average_of([10000, None, 12000, None, 14000]) is None


def test_ao12_allows_one_dnf_only():
    times = [10000 + i * 100 for i in range(12)]
    one = times[:]
    one[3] = None
    two = times[:]
    two[3] = None
    two[7] = None
    assert averages.average_of(one) is not None
    assert averages.average_of(two) is None


def test_ao100_allows_five_dnfs_only():
    five = [10000] * 95 + [None] * 5
    six = [10000] * 94 + [None] * 6
    assert averages.average_of(five) == 10000
    assert averages.average_of(six) is None


def test_rounds_half_up_to_centisecond():
    assert averages.average_of([10000, 12665, 12665, 12665, 20000]) == 12670
    assert averages.average_of([10000, 12664, 12664, 12664, 20000]) == 12660


def test_fewer_than_five_times_raises():
    with pytest.raises(ValueError):
        averages.average_of([10000, 11000, 12000, 13000])
