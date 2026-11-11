"""Random-move 3x3 scrambles.

This is NOT a WCA random-state scramble: it picks random moves with simple
rules instead of sampling a uniformly random cube state.
"""
import random

FACES = ("U", "D", "L", "R", "F", "B")
AXIS = {"U": 0, "D": 0, "L": 1, "R": 1, "F": 2, "B": 2}
MODIFIERS = ("", "'", "2")


def generate_scramble(length=20, rng=None):
    """Return `length` random moves, never two in a row on the same axis.

    `rng` can be a seeded random.Random so tests are reproducible.
    """
    if length < 1:
        raise ValueError("length must be at least 1")
    rng = random if rng is None else rng
    moves = []
    last_axis = None
    for _ in range(length):
        face = rng.choice([f for f in FACES if AXIS[f] != last_axis])
        moves.append(face + rng.choice(MODIFIERS))
        last_axis = AXIS[face]
    return " ".join(moves)
