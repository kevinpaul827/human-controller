from __future__ import annotations

import math

import numpy as np

from ..core.angles import AngleKey, AngleWindow, reduce_joints, valid_values
from ..core.types import GestureTemplate

Rep = AngleWindow

# A joint must move this far to be included; all saved reps use this frame count.
MIN_ACTIVE_RANGE_DEG = 15.0
MOTION_TRAJECTORY_FRAMES = 32

def _resample_joint(series: list[float | None], n_out: int) -> list[float | None]:
    """Linearly resample one joint's angle series to ``n_out`` frames.

    Masked (``None``) samples are interpolated over when neighbours exist; if the
    joint has no valid samples at all, the output stays ``None``.
    """
    idx = [i for i, v in enumerate(series) if v is not None]
    if not idx:
        return [None] * n_out
    xs = np.array(idx, dtype=np.float64)
    ys = np.array([float(series[i]) for i in idx], dtype=np.float64)  # type: ignore[arg-type]
    # Map the n_out output positions onto the original [0, len-1] index range.
    targets = np.linspace(0.0, len(series) - 1, n_out)
    return [float(v) for v in np.interp(targets, xs, ys)]


def _resample_rep(rep: Rep, n_out: int) -> Rep:
    columns = {j: _resample_joint([f.get(j) for f in rep], n_out) for j in AngleKey}
    return [{j: columns[j][t] for j in AngleKey} for t in range(n_out)]


class TemplateBuilder:
    def __init__(
        self,
        min_active_range_deg: float = MIN_ACTIVE_RANGE_DEG,
        motion_trajectory_frames: int = MOTION_TRAJECTORY_FRAMES,
    ) -> None:
        if (
            isinstance(motion_trajectory_frames, bool)
            or not isinstance(motion_trajectory_frames, int)
            or motion_trajectory_frames < 2
        ):
            raise ValueError("motion_trajectory_frames must be at least 2.")
        if not math.isfinite(min_active_range_deg) or min_active_range_deg < 0.0:
            raise ValueError("min_active_range_deg must be non-negative and finite.")
        self.min_active_range_deg = min_active_range_deg
        self.motion_trajectory_frames = motion_trajectory_frames

    def detect_active_joints(self, reps: list[Rep]) -> list[AngleKey]:
        flat = [frame for rep in reps for frame in rep]
        ranges = reduce_joints(flat, lambda v: max(v) - min(v))
        return [
            j for j, r in ranges.items()
            if r is not None and r >= self.min_active_range_deg
        ]

    def build_motion(
        self,
        reps: list[Rep],
        name: str,
        fps: int = 30,
        active_joints: list[AngleKey] | None = None,
    ) -> GestureTemplate:
        self._validate_build_inputs(reps, name, fps)
        name = str(name).strip()
        active_joints = self._resolve_active_joints(reps, active_joints)
        n = self.motion_trajectory_frames
        resampled = [_resample_rep(rep, n) for rep in reps]

        trajectory: AngleWindow = []
        for t in range(n):
            frame_vals = [rep[t] for rep in resampled]
            mean_frame = reduce_joints(frame_vals, np.mean)
            trajectory.append(
                {j: mean_frame[j] for j in active_joints if mean_frame[j] is not None}
            )
        return GestureTemplate(
            name=name,
            active_joints=list(active_joints),
            trajectory=trajectory,
            fps=fps,
        )

    def _resolve_active_joints(
        self, reps: list[Rep], active_joints: list[AngleKey] | None
    ) -> list[AngleKey]:
        """Caller-supplied joints, else the moving ones, else any with full data."""
        if active_joints is None:
            active_joints = self.detect_active_joints(reps)
        return active_joints or self._joints_with_data(reps)

    def _joints_with_data(self, reps: list[Rep]) -> list[AngleKey]:
        return [
            j for j in AngleKey
            if all(valid_values(frame.get(j) for frame in rep) for rep in reps)
        ]

    @staticmethod
    def _validate_build_inputs(reps: list[Rep], name: str, fps: int) -> None:
        if not reps:
            raise ValueError("Need at least one repetition to build a template.")
        if any(not rep for rep in reps):
            raise ValueError("Repetitions must contain at least one frame.")
        for rep in reps:
            for frame in rep:
                for value in frame.values():
                    if value is not None and not math.isfinite(float(value)):
                        raise ValueError("Repetition angle values must be finite.")
        if not str(name).strip():
            raise ValueError("Gesture template name is required.")
        if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
            raise ValueError("Gesture template FPS must be a positive integer.")
