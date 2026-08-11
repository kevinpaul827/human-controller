"""validation.py

Validates a value and makes sure it's
between two bounds. Otherwise, return
a default value.
"""

from __future__ import annotations

import math


def bounded_number(
    value: object,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return min(maximum, max(minimum, number))
