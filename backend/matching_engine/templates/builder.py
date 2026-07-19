from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from ..core.angles import AngleKey, AngleVector, reduce_joints, valid_values
from ..core.types import GestureTemplate

Rep = List[AngleVector]

END_STATE_FRAMES = 5
MIN_ACTIVE_RANGE_DEG = 15.0
TOLERANCE_K = 2.0
MIN_TOLERANCE_DEG = 5.0

# Number of frames every motion trajectory is resampled to, so reps performed at
# different speeds/lengths can be averaged and later DTW-matched consistently.
MOTION_TRAJECTORY_FRAMES = 32


def _end_state(rep: Rep, n_frames: int) -> AngleVector:
    tail = rep[-n_frames:] if len(rep) >= n_frames else rep
    return reduce_joints(tail, np.mean)


def _resample_joint(series: List[Optional[float]], n_out: int) -> List[Optional[float]]:
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
        end_state_frames: int = END_STATE_FRAMES,
        min_active_range_deg: float = MIN_ACTIVE_RANGE_DEG,
        tolerance_k: float = TOLERANCE_K,
        min_tolerance_deg: float = MIN_TOLERANCE_DEG,
        motion_trajectory_frames: int = MOTION_TRAJECTORY_FRAMES,
    ) -> None:
        self.end_state_frames = end_state_frames
        self.min_active_range_deg = min_active_range_deg
        self.tolerance_k = tolerance_k
        self.min_tolerance_deg = min_tolerance_deg
        self.motion_trajectory_frames = motion_trajectory_frames

    def detect_active_joints(self, reps: List[Rep]) -> List[AngleKey]:
        flat = [frame for rep in reps for frame in rep]
        ranges = reduce_joints(flat, lambda v: max(v) - min(v))
        return [
            j for j, r in ranges.items()
            if r is not None and r >= self.min_active_range_deg
        ]

    def build(
        self,
        reps: List[Rep],
        name: str,
        mode: str = "state",
        fps: int = 30,
        active_joints: Optional[List[AngleKey]] = None,
    ) -> GestureTemplate:
        if not reps:
            raise ValueError("Need at least one repetition to build a template.")
        if mode == "state":
            return self._build_state(reps, name, fps, active_joints)
        if mode == "motion":
            return self._build_motion(reps, name, fps, active_joints)
        raise NotImplementedError(f"Unknown template mode: {mode!r}")

    def _build_state(
        self,
        reps: List[Rep],
        name: str,
        fps: int,
        active_joints: Optional[List[AngleKey]],
    ) -> GestureTemplate:
        if active_joints is None:
            active_joints = self.detect_active_joints(reps)
        if not active_joints:
            active_joints = self._joints_with_data(reps)

        end_states = [self._end_state(rep) for rep in reps]

        target_angles: Dict[AngleKey, float] = {}
        tolerance_deg: Dict[AngleKey, float] = {}
        for joint in active_joints:
            per_rep = valid_values(es.get(joint) for es in end_states)
            if not per_rep:
                continue
            target_angles[joint] = float(np.mean(per_rep))
            std = float(np.std(per_rep)) if len(per_rep) > 1 else 0.0
            tolerance_deg[joint] = max(self.tolerance_k * std, self.min_tolerance_deg)

        active = [j for j in active_joints if j in target_angles]

        return GestureTemplate(
            name=name,
            type="state",
            active_joints=active,
            target_angles=target_angles,
            tolerance_deg=tolerance_deg,
            trajectory=[],
            fps=fps,
        )

    def _build_motion(
        self,
        reps: List[Rep],
        name: str,
        fps: int,
        active_joints: Optional[List[AngleKey]],
    ) -> GestureTemplate:
        """Build a movement template: a mean, time-normalised joint-angle path.

        Each rep is resampled to a common length so reps of differing speed can
        be averaged frame-by-frame into a single reference ``trajectory`` that
        ``MotionMatcher`` scores live windows against via DTW. Per-joint
        tolerances are derived from inter-rep variance along the path.
        """
        if active_joints is None:
            active_joints = self.detect_active_joints(reps)
        if not active_joints:
            active_joints = self._joints_with_data(reps)

        n = self.motion_trajectory_frames
        resampled = [_resample_rep(rep, n) for rep in reps]

        trajectory: List[Dict[str, Any]] = []
        frame_stds: Dict[AngleKey, List[float]] = {j: [] for j in active_joints}
        for t in range(n):
            frame_vals = [rep[t] for rep in resampled]
            mean_frame = reduce_joints(frame_vals, np.mean)
            trajectory.append(
                {j.value: mean_frame[j] for j in active_joints if mean_frame[j] is not None}
            )
            for j in active_joints:
                per_rep = valid_values(f.get(j) for f in frame_vals)
                if len(per_rep) > 1:
                    frame_stds[j].append(float(np.std(per_rep)))

        tolerance_deg: Dict[AngleKey, float] = {}
        for j in active_joints:
            mean_std = float(np.mean(frame_stds[j])) if frame_stds[j] else 0.0
            tolerance_deg[j] = max(self.tolerance_k * mean_std, self.min_tolerance_deg)

        return GestureTemplate(
            name=name,
            type="motion",
            active_joints=list(active_joints),
            target_angles={},
            tolerance_deg=tolerance_deg,
            trajectory=trajectory,
            fps=fps,
        )

    def _end_state(self, rep: Rep) -> AngleVector:
        return _end_state(rep, self.end_state_frames)

    def _joints_with_data(self, reps: List[Rep]) -> List[AngleKey]:
        return [
            j for j in AngleKey
            if all(valid_values(frame.get(j) for frame in rep) for rep in reps)
        ]
