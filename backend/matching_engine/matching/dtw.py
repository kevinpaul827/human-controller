from __future__ import annotations

import math
from typing import Literal

import numpy as np

from ..core.angles import AngleKey, AngleVector, AngleWindow

MISS_PENALTY_DEG = 180.0
StepPattern = Literal["symmetric1", "symmetric2", "symmetricP1"]
DEFAULT_STEP_PATTERN: StepPattern = "symmetricP1"

Production = tuple[tuple[int, int], tuple[tuple[int, int, float], ...]]
STEP_PATTERNS: dict[StepPattern, tuple[Production, ...]] = {
    "symmetric1": (
        ((1, 1), (((0, 0), 1.0),)),
        ((1, 0), (((0, 0), 1.0),)),
        ((0, 1), (((0, 0), 1.0),)),
    ),
    "symmetric2": (
        ((1, 1), (((0, 0), 2.0),)),
        ((1, 0), (((0, 0), 1.0),)),
        ((0, 1), (((0, 0), 1.0),)),
    ),
    "symmetricP1": (
        ((1, 2), (((0, 1), 2.0), ((0, 0), 1.0))),
        ((1, 1), (((0, 0), 2.0),)),
        ((2, 1), (((1, 0), 2.0), ((0, 0), 1.0))),
    ),
}


def frame_cost(
    a: AngleVector,
    b: AngleVector,
    joints: list[AngleKey],
) -> float | None:
    diffs: list[float] = []
    for joint in joints:
        va = a.get(joint)
        vb = b.get(joint)
        if va is None or vb is None:
            continue
        diffs.append(abs(float(va) - float(vb)))
    if not diffs:
        return None
    return sum(diffs) / len(diffs)


def _band_bounds(i: int, n: int, m: int, band: int) -> tuple[int, int]:
    center = i * m / n
    lo = max(1, int(np.floor(center - band)))
    hi = min(m, int(np.ceil(center + band)))
    return lo, hi


def dtw_distance(
    seq_a: AngleWindow,
    seq_b: AngleWindow,
    joints: list[AngleKey],
    band: int | None = None,
    miss_penalty: float = MISS_PENALTY_DEG,
    step_pattern: StepPattern = DEFAULT_STEP_PATTERN,
    open_begin: bool = False,
) -> float:
    if step_pattern not in STEP_PATTERNS:
        raise ValueError(f"Unsupported DTW step pattern: {step_pattern!r}")
    if band is not None and (
        isinstance(band, bool) or not isinstance(band, int) or band < 0
    ):
        raise ValueError("DTW band must be a non-negative integer or None.")
    if not math.isfinite(miss_penalty) or miss_penalty < 0.0:
        raise ValueError("DTW miss penalty must be a non-negative finite number.")
    n, m = len(seq_a), len(seq_b)
    if n == 0 or m == 0:
        return float("inf")
    productions = STEP_PATTERNS[step_pattern]

    lcost: dict[tuple[int, int], float] = {}

    def local(i: int, j: int) -> float:
        v = lcost.get((i, j))
        if v is None:
            c = frame_cost(seq_a[i - 1], seq_b[j - 1], joints)
            v = miss_penalty if c is None else c
            lcost[(i, j)] = v
        return v

    acc = np.full((n + 1, m + 1), np.inf)
    wacc = np.zeros((n + 1, m + 1))
    acc[0, 0] = 0.0
    if open_begin:
        acc[:, 0] = 0.0

    for i in range(1, n + 1):
        lo, hi = (1, m) if band is None else _band_bounds(i, n, m, band)
        for j in range(lo, hi + 1):
            best, best_w = np.inf, 0.0
            for (di, dj), cells in productions:
                pi, pj = i - di, j - dj
                if pi < 0 or pj < 0 or not np.isfinite(acc[pi, pj]):
                    continue
                extra = sum(w * local(i - ci, j - cj) for (ci, cj), w in cells)
                cand = acc[pi, pj] + extra
                if cand < best:
                    best = cand
                    best_w = wacc[pi, pj] + sum(w for _, w in cells)
            acc[i, j] = best
            wacc[i, j] = best_w

    total, weight = acc[n, m], wacc[n, m]
    if not np.isfinite(total) or weight == 0:
        return float("inf")
    return float(total) / float(weight)
