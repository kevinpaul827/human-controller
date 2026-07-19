from __future__ import annotations

from typing import Dict, Optional

from .core.angles import AngleKey, AngleVector


class AngleSmoother:
    def __init__(self, alpha: float = 0.25, deadband_deg: float = 2.0) -> None:
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        if deadband_deg < 0.0:
            raise ValueError("deadband_deg must be >= 0")
        self.alpha = alpha
        self.deadband_deg = deadband_deg
        self._state: Dict[AngleKey, Optional[float]] = {}

    def update(self, angles: AngleVector) -> AngleVector:
        out: AngleVector = {}
        for joint in AngleKey:
            cur = angles.get(joint)
            if cur is None:
                self._state[joint] = None
                out[joint] = None
                continue
            prev = self._state.get(joint)
            if prev is None:
                val = cur
            elif abs(cur - prev) < self.deadband_deg:
                val = prev  # deadband
            else:
                val = prev + self.alpha * (cur - prev)
            self._state[joint] = val
            out[joint] = val
        return out

    def reset(self) -> None:
        self._state = {}
