from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from ..core.angles import AngleKey, AngleVector, reduce_joints, valid_values
from ..core.types import GestureTemplate

Rep = List[AngleVector]

END_STATE_FRAMES = 5
MIN_ACTIVE_RANGE_DEG = 15.0
TOLERANCE_K = 2.0
MIN_TOLERANCE_DEG = 5.0


def _end_state(rep: Rep, n_frames: int) -> AngleVector:
    tail = rep[-n_frames:] if len(rep) >= n_frames else rep
    return reduce_joints(tail, np.mean)


class TemplateBuilder:
    def __init__(
        self,
        end_state_frames: int = END_STATE_FRAMES,
        min_active_range_deg: float = MIN_ACTIVE_RANGE_DEG,
        tolerance_k: float = TOLERANCE_K,
        min_tolerance_deg: float = MIN_TOLERANCE_DEG,
    ) -> None:
        self.end_state_frames = end_state_frames
        self.min_active_range_deg = min_active_range_deg
        self.tolerance_k = tolerance_k
        self.min_tolerance_deg = min_tolerance_deg

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
        if mode != "state":
            raise NotImplementedError(
                "TemplateBuilder v1 only supports 'state' templates"
            )
        if not reps:
            raise ValueError("Need at least one repetition to build a template.")

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

    def _end_state(self, rep: Rep) -> AngleVector:
        return _end_state(rep, self.end_state_frames)

    def _joints_with_data(self, reps: List[Rep]) -> List[AngleKey]:
        return [
            j for j in AngleKey
            if all(valid_values(frame.get(j) for frame in rep) for rep in reps)
        ]
