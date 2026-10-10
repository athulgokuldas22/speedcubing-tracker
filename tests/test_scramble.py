import random
import re

import pytest

from solves.scramble import AXIS, generate_scramble

MOVE = re.compile(r"^[UDLRFB]['2]?$")


def test_default_length_is_20():
    assert len(generate_scramble().split()) == 20


def test_custom_length():
    assert len(generate_scramble(length=25).split()) == 25


def test_invalid_length_raises():
    with pytest.raises(ValueError):
        generate_scramble(length=0)


def test_every_token_is_a_valid_move():
    for _ in range(200):
        assert all(MOVE.match(m) for m in generate_scramble().split())


def test_no_two_consecutive_moves_on_the_same_axis():
    for _ in range(200):
        moves = generate_scramble().split()
        for a, b in zip(moves, moves[1:]):
            assert AXIS[a[0]] != AXIS[b[0]]


def test_seeded_rng_is_reproducible():
    first = generate_scramble(rng=random.Random(42))
    second = generate_scramble(rng=random.Random(42))
    assert first == second


def test_different_seeds_give_different_scrambles():
    assert generate_scramble(rng=random.Random(1)) != generate_scramble(rng=random.Random(2))
