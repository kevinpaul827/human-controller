"""DTW motion matcher (v2): weighted, slope-constrained, windowed DTW.

Compares a live window of angle vectors against a template trajectory using a
step-pattern-weighted flexible DTW (S-WFDTW): a weighted step pattern with a
slope constraint plus an optional Sakoe-Chiba window, so scoring is robust to
speed differences while resisting degenerate/singular alignments. Implements the
same ``MatcherStrategy`` Protocol as ``PoseMatcher``.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..core.angles import AngleKey, AngleVector
from ..core.types import GestureTemplate, MatchResult

DEFAULT_MOTION_TOLERANCE_DEG = 30.0
MISS_PENALTY_DEG = 180.0
DEFAULT_STEP_PATTERN = "symmetricP1"

AngleWindow = List[AngleVector]

# (predecessor (di, dj), [(local_cell (ci, cj), weight), ...]); local cell is
# offset back from the current (i, j). Weighted path length is always n + m.
Production = Tuple[Tuple[int, int], Tuple[Tuple[int, int, float], ...]]
STEP_PATTERNS: Dict[str, Tuple[Production, ...]] = {
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


def _frame_cost(a: AngleVector, b: AngleVector, joints: List[AngleKey]) -> Optional[float]:
    diffs: List[float] = []
    for joint in joints:
        va = a.get(joint)
        vb = b.get(joint)
        if va is None or vb is None:
            continue
        diffs.append(abs(float(va) - float(vb)))
    if not diffs:
        return None
    return sum(diffs) / len(diffs)


def _band_bounds(i: int, n: int, m: int, band: int) -> Tuple[int, int]:
    center = i * m / n
    lo = max(1, int(np.floor(center - band)))
    hi = min(m, int(np.ceil(center + band)))
    return lo, hi


def dtw_distance(
    seq_a: AngleWindow,
    seq_b: AngleWindow,
    joints: List[AngleKey],
    band: Optional[int] = None,
    miss_penalty: float = MISS_PENALTY_DEG,
    step_pattern: str = DEFAULT_STEP_PATTERN,
    open_begin: bool = False,
) -> float:
    """Weight-normalised DTW distance (avg degrees of error per aligned step).

    ``symmetricP1`` enforces a slope in [1/2, 2] (out-of-ratio pairs return
    ``inf``); ``symmetric2`` allows any speed ratio. ``band`` adds a Sakoe-Chiba
    window. ``open_begin`` matches ``seq_b`` against the best-aligned *tail* of
    ``seq_a`` (subsequence DTW), skipping leading ``seq_a`` frames for free.
    """
    n, m = len(seq_a), len(seq_b)
    if n == 0 or m == 0:
        return float("inf")
    productions = STEP_PATTERNS[step_pattern]

    lcost: Dict[Tuple[int, int], float] = {}

    def local(i: int, j: int) -> float:
        v = lcost.get((i, j))
        if v is None:
            c = _frame_cost(seq_a[i - 1], seq_b[j - 1], joints)
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


def _trajectory_to_window(trajectory: List[Dict[str, object]]) -> AngleWindow:
    """Convert a template's serialisable ``trajectory`` into an AngleWindow."""
    window: AngleWindow = []
    for frame in trajectory:
        vec: AngleVector = {}
        for key, value in frame.items():
            vec[AngleKey(key)] = None if value is None else float(value)  # type: ignore[arg-type]
        window.append(vec)
    return window


def _template_joints(template: GestureTemplate, ref: AngleWindow) -> List[AngleKey]:
    if template.active_joints:
        return list(template.active_joints)
    seen: List[AngleKey] = []
    for frame in ref:
        for joint, value in frame.items():
            if value is not None and joint not in seen:
                seen.append(joint)
    return seen


def _joint_range(window: AngleWindow, joint: AngleKey) -> float:
    vals = [f[joint] for f in window if f.get(joint) is not None]
    return (max(vals) - min(vals)) if len(vals) >= 2 else 0.0


class MotionMatcher:
    """S-WFDTW matcher for movement (trajectory) gesture templates."""

    def __init__(
        self,
        band: Optional[int] = None,
        default_tolerance_deg: float = DEFAULT_MOTION_TOLERANCE_DEG,
        step_pattern: str = DEFAULT_STEP_PATTERN,
        open_begin: bool = False,
        min_amplitude_ratio: float = 0.0,
        end_pose_tol_deg: Optional[float] = None,
    ) -> None:
        self.band = band
        self.default_tolerance_deg = default_tolerance_deg
        self.step_pattern = step_pattern
        self.open_begin = open_begin
        self.min_amplitude_ratio = min_amplitude_ratio
        self.end_pose_tol_deg = end_pose_tol_deg

    def score(self, current: AngleWindow, template: GestureTemplate) -> float:
        ref = _trajectory_to_window(template.trajectory)
        if not ref or not current:
            return 0.0

        joints = _template_joints(template, ref)
        if not joints:
            return 0.0

        if self.min_amplitude_ratio > 0.0:
            for j in joints:
                tmpl_range = _joint_range(ref, j)
                if tmpl_range >= 1e-6 and _joint_range(current, j) < self.min_amplitude_ratio * tmpl_range:
                    return 0.0

        if self.end_pose_tol_deg is not None:
            end_ref, end_cur = ref[-1], current[-1]
            for j in joints:
                rv, cv = end_ref.get(j), end_cur.get(j)
                if rv is not None and cv is not None and abs(cv - rv) > self.end_pose_tol_deg:
                    return 0.0

        dist = dtw_distance(
            current,
            ref,
            joints,
            band=self.band,
            step_pattern=self.step_pattern,
            open_begin=self.open_begin,
        )
        if not np.isfinite(dist):
            return 0.0

        scale = max(self.default_tolerance_deg, 1e-6)
        return float(max(0.0, min(1.0, 1.0 - dist / scale)))

    def best_match(
        self,
        current: AngleWindow,
        templates: List[GestureTemplate],
        timestamp: Optional[float] = None,
    ) -> Optional[MatchResult]:
        ts = time.time() if timestamp is None else timestamp
        best: Optional[MatchResult] = None
        for template in templates:
            s = self.score(current, template)
            if best is None or s > best.score:
                best = MatchResult(gesture_id=template.gesture_id, score=s, timestamp=ts)
        return best
