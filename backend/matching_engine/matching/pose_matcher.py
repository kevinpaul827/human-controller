"""v1 joint-angle state matcher."""

from __future__ import annotations

import time
from typing import List, Optional

from ..core.angles import AngleKey, AngleVector
from ..core.types import GestureTemplate, MatchResult

DEFAULT_TOLERANCE_DEG = 15.0


def state_score(
    current: AngleVector,
    target_angles: dict[AngleKey, float],
    tolerance_deg: dict[AngleKey, float],
) -> float:
    closeness: List[float] = []
    for joint, target in target_angles.items():
        value = current.get(joint)
        if value is None:
            continue
        tol = max(tolerance_deg.get(joint, DEFAULT_TOLERANCE_DEG), 1e-6)  # avoid division by zero
        closeness.append(max(0.0, 1.0 - abs(value - target) / tol))
    return min(closeness) if closeness else 0.0


class PoseMatcher:
    def score(self, current: AngleVector, template: GestureTemplate) -> float:
        return state_score(current, template.target_angles, template.tolerance_deg)

    def best_match(
        self,
        current: AngleVector,
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
