"""Gesture template and match result type definitions"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import uuid4

from .angles import AngleKey, AngleVector, AngleWindow

__all__ = [
    "AngleKey",
    "AngleVector",
    "MatchResult",
    "GestureTemplate",
    "MOTION_TYPE",
    "SCHEMA_VERSION",
]

SCHEMA_VERSION = 2
DEFAULT_FPS = 30
MOTION_TYPE = "motion"

def _finite_float(value: object, field_name: str) -> float:
    resolved = float(value)
    if not math.isfinite(resolved):
        raise ValueError(f"{field_name} values must be finite.")
    return resolved


@dataclass
class MatchResult:
    gesture_id: str
    score: float
    timestamp: float


@dataclass
class GestureTemplate:
    name: str
    gesture_id: str = field(default_factory=lambda: uuid4().hex)
    active_joints: list[AngleKey] = field(default_factory=list)
    trajectory: AngleWindow = field(default_factory=list)
    fps: int = DEFAULT_FPS

    def __post_init__(self) -> None:
        self.name = str(self.name).strip()
        self.gesture_id = str(self.gesture_id).strip()
        if not self.name:
            raise ValueError("Gesture template name is required.")
        if not self.gesture_id:
            raise ValueError("Gesture template ID is required.")
        self.active_joints = [AngleKey(joint) for joint in self.active_joints]
        normalized_trajectory: AngleWindow = []
        for frame in self.trajectory:
            normalized_trajectory.append(
                {
                    AngleKey(joint): (
                        None
                        if value is None
                        else _finite_float(value, "trajectory")
                    )
                    for joint, value in frame.items()
                }
            )
        self.trajectory = normalized_trajectory
        if isinstance(self.fps, bool) or not isinstance(self.fps, int) or self.fps <= 0:
            raise ValueError("Gesture template FPS must be a positive integer.")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "gesture_id": self.gesture_id,
            "name": self.name,
            "type": MOTION_TYPE,
            "active_joints": [j.value for j in self.active_joints],
            "trajectory": [
                {
                    joint.value: None if value is None else float(value)
                    for joint, value in frame.items()
                }
                for frame in self.trajectory
            ],
            "fps": self.fps,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "GestureTemplate":
        version = int(payload.get("schema_version", SCHEMA_VERSION))
        if version != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported gesture template schema version: {version!r}"
            )
        if payload.get("type", MOTION_TYPE) != MOTION_TYPE:
            raise ValueError("Only motion gesture templates are supported.")
        active_joints = payload.get("active_joints", [])
        trajectory = payload.get("trajectory", [])
        if not isinstance(active_joints, list):
            raise ValueError("active_joints must be a list.")
        if not isinstance(trajectory, list) or any(
            not isinstance(frame, Mapping) for frame in trajectory
        ):
            raise ValueError("trajectory must be a list of objects.")
        return cls(
            name=str(payload.get("name", "")),
            gesture_id=str(payload.get("gesture_id", "")),
            active_joints=[AngleKey(str(joint)) for joint in active_joints],
            trajectory=[dict(frame) for frame in trajectory],
            fps=int(payload.get("fps", DEFAULT_FPS)),
        )
