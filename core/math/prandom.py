from random import random
from core.Typing import TYPE_FLOAT
from beartype import beartype


__all__ = [
    "randf"
]


@beartype
def randf(a: TYPE_FLOAT, b: TYPE_FLOAT) -> float:
    return random() * (b - a) + a
