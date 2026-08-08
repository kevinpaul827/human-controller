"""Gesture template and match result type definitions"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import uuid4

from .angles import AngleKey, AngleVector

__all__ = [
    "AngleKey",
    "AngleVector",
    "MatchResult",
    "GestureTemplate",
    "SCHEMA_VERSION",
]

SCHEMA_VERSION = 2

# Shared by the dataclass defaults and the from_dict fallbacks, so the two
# can't disagree about what an omitted field means.
DEFAULT_TYPE = "state"
DEFAULT_FPS = 30


@dataclass
class MatchResult:
    gesture_id: str
    score: float
    timestamp: float


@dataclass
class GestureTemplate:
    name: str
    gesture_id: str = field(default_factory=lambda: uuid4().hex)
    type: str = DEFAULT_TYPE
    active_joints: List[AngleKey] = field(default_factory=list)
    target_angles: Dict[AngleKey, float] = field(default_factory=dict)
    tolerance_deg: Dict[AngleKey, float] = field(default_factory=dict)
    trajectory: List[Dict[str, Any]] = field(default_factory=list)
    fps: int = DEFAULT_FPS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gesture_id": self.gesture_id,
            "name": self.name,
            "type": self.type,
            "active_joints": [j.value for j in self.active_joints],
            "target_angles": {k.value: float(v) for k, v in self.target_angles.items()},
            "tolerance_deg": {k.value: float(v) for k, v in self.tolerance_deg.items()},
            "trajectory": self.trajectory,
            "fps": self.fps,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GestureTemplate":
        return cls(
            name=d["name"],
            gesture_id=d["gesture_id"],
            type=d.get("type", DEFAULT_TYPE),
            active_joints=[AngleKey(j) for j in d.get("active_joints", [])],
            target_angles={AngleKey(k): float(v) for k, v in d.get("target_angles", {}).items()},
            tolerance_deg={AngleKey(k): float(v) for k, v in d.get("tolerance_deg", {}).items()},
            trajectory=d.get("trajectory", []),
            fps=int(d.get("fps", DEFAULT_FPS)),
        )
