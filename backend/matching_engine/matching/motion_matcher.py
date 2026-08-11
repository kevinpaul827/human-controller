"""Match live movement against saved gesture templates."""

from __future__ import annotations

import math

import numpy as np

from ..core.angles import AngleKey, AngleWindow
from ..core.types import GestureTemplate, MatchResult
from .dtw import (
    DEFAULT_STEP_PATTERN,
    STEP_PATTERNS,
    StepPattern,
    dtw_distance,
    frame_cost,
)
from .strategy import best_of

DEFAULT_MOTION_TOLERANCE_DEG = 30.0

def _template_joints(template: GestureTemplate, ref: AngleWindow) -> list[AngleKey]:
    if template.active_joints:
        return list(template.active_joints)
    seen: list[AngleKey] = []
    for frame in ref:
        for joint, value in frame.items():
            if value is not None and joint not in seen:
                seen.append(joint)
    return seen


def _joint_range(window: AngleWindow, joint: AngleKey) -> float:
    vals = [f[joint] for f in window if f.get(joint) is not None]
    return (max(vals) - min(vals)) if len(vals) >= 2 else 0.0


def _covers_trajectory(
    current: AngleWindow,
    reference: AngleWindow,
    joints: list[AngleKey],
    tolerance_deg: float,
) -> bool:
    current_index = 0
    for reference_frame in reference:
        while current_index < len(current):
            cost = frame_cost(
                current[current_index],
                reference_frame,
                joints,
            )
            if cost is not None and cost <= tolerance_deg:
                break
            current_index += 1
        if current_index == len(current):
            return False
    return True


class MotionMatcher:
    def __init__(
        self,
        band: int | None = None,
        default_tolerance_deg: float = DEFAULT_MOTION_TOLERANCE_DEG,
        step_pattern: StepPattern = DEFAULT_STEP_PATTERN,
        open_begin: bool = False,
        min_amplitude_ratio: float = 0.0,
        end_pose_tol_deg: float | None = None,
        min_template_range_deg: float = 0.0,
        coverage_tol_deg: float | None = None,
    ) -> None:
        if band is not None and (
            isinstance(band, bool) or not isinstance(band, int) or band < 0
        ):
            raise ValueError("band must be a non-negative integer or None.")
        if not math.isfinite(default_tolerance_deg) or default_tolerance_deg <= 0.0:
            raise ValueError("default_tolerance_deg must be positive and finite.")
        if step_pattern not in STEP_PATTERNS:
            raise ValueError(f"Unsupported DTW step pattern: {step_pattern!r}")
        if (
            not math.isfinite(min_amplitude_ratio)
            or not 0.0 <= min_amplitude_ratio <= 1.0
        ):
            raise ValueError("min_amplitude_ratio must be between 0 and 1.")
        for field_name, value in (
            ("end_pose_tol_deg", end_pose_tol_deg),
            ("min_template_range_deg", min_template_range_deg),
            ("coverage_tol_deg", coverage_tol_deg),
        ):
            if value is not None and (not math.isfinite(value) or value < 0.0):
                raise ValueError(f"{field_name} must be non-negative and finite.")
        self.band = band
        self.default_tolerance_deg = default_tolerance_deg
        self.step_pattern = step_pattern
        self.open_begin = open_begin
        self.min_amplitude_ratio = min_amplitude_ratio
        self.end_pose_tol_deg = end_pose_tol_deg
        self.min_template_range_deg = min_template_range_deg
        self.coverage_tol_deg = coverage_tol_deg

    def _scored_joints(
        self,
        template: GestureTemplate,
        ref: AngleWindow,
    ) -> list[AngleKey]:
        joints = _template_joints(template, ref)
        if self.min_template_range_deg <= 0.0:
            return joints
        return [j for j in joints if _joint_range(ref, j) >= self.min_template_range_deg]

    def _rejected(
        self,
        current: AngleWindow,
        ref: AngleWindow,
        joints: list[AngleKey],
    ) -> bool:
        if self.min_amplitude_ratio > 0.0:
            for j in joints:
                tmpl_range = _joint_range(ref, j)
                current_range = _joint_range(current, j)
                if (
                    tmpl_range >= 1e-6
                    and current_range < self.min_amplitude_ratio * tmpl_range
                ):
                    return True

        if self.end_pose_tol_deg is not None:
            end_ref, end_cur = ref[-1], current[-1]
            for j in joints:
                rv, cv = end_ref.get(j), end_cur.get(j)
                if (
                    rv is not None
                    and cv is not None
                    and abs(cv - rv) > self.end_pose_tol_deg
                ):
                    return True

        if self.coverage_tol_deg is not None:
            return not _covers_trajectory(current, ref, joints, self.coverage_tol_deg)

        return False

    def score(self, current: AngleWindow, template: GestureTemplate) -> float:
        ref = template.trajectory
        if not ref or not current:
            return 0.0

        joints = self._scored_joints(template, ref)
        if not joints or self._rejected(current, ref, joints):
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
        templates: list[GestureTemplate],
        timestamp: float | None = None,
    ) -> MatchResult | None:
        return best_of(lambda t: self.score(current, t), templates, timestamp)
