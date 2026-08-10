"""Joint-angle feature extraction from BlazePose keypoints"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from enum import Enum

import numpy as np

from backend.pose_types import (
    MEASURABLE_REGIONS,
    BodyRegion,
    PoseKeypoint,
    PoseLandmarks,
)

# Landmark confidence required before an angle measurement is used.
VIS_FLOOR = 0.5

class AngleKey(str, Enum):
    L_ELBOW = "L_ELBOW"
    R_ELBOW = "R_ELBOW"
    L_SHOULDER_ABD = "L_SHOULDER_ABD"
    R_SHOULDER_ABD = "R_SHOULDER_ABD"
    L_KNEE = "L_KNEE"
    R_KNEE = "R_KNEE"
    L_HIP = "L_HIP"
    R_HIP = "R_HIP"
    L_ANKLE = "L_ANKLE"
    R_ANKLE = "R_ANKLE"


ANGLE_TRIPLETS: dict[AngleKey, tuple[PoseKeypoint, PoseKeypoint, PoseKeypoint]] = {
    AngleKey.L_ELBOW: (
        PoseKeypoint.L_SHOULDER,
        PoseKeypoint.L_ELBOW,
        PoseKeypoint.L_WRIST,
    ),
    AngleKey.R_ELBOW: (
        PoseKeypoint.R_SHOULDER,
        PoseKeypoint.R_ELBOW,
        PoseKeypoint.R_WRIST,
    ),
    AngleKey.L_SHOULDER_ABD: (
        PoseKeypoint.L_HIP,
        PoseKeypoint.L_SHOULDER,
        PoseKeypoint.L_ELBOW,
    ),
    AngleKey.R_SHOULDER_ABD: (
        PoseKeypoint.R_HIP,
        PoseKeypoint.R_SHOULDER,
        PoseKeypoint.R_ELBOW,
    ),
    AngleKey.L_KNEE: (PoseKeypoint.L_HIP, PoseKeypoint.L_KNEE, PoseKeypoint.L_ANKLE),
    AngleKey.R_KNEE: (PoseKeypoint.R_HIP, PoseKeypoint.R_KNEE, PoseKeypoint.R_ANKLE),
    AngleKey.L_HIP: (PoseKeypoint.L_SHOULDER, PoseKeypoint.L_HIP, PoseKeypoint.L_KNEE),
    AngleKey.R_HIP: (PoseKeypoint.R_SHOULDER, PoseKeypoint.R_HIP, PoseKeypoint.R_KNEE),
    AngleKey.L_ANKLE: (
        PoseKeypoint.L_KNEE,
        PoseKeypoint.L_ANKLE,
        PoseKeypoint.L_FOOT_INDEX,
    ),
    AngleKey.R_ANKLE: (
        PoseKeypoint.R_KNEE,
        PoseKeypoint.R_ANKLE,
        PoseKeypoint.R_FOOT_INDEX,
    ),
}

AngleVector = dict[AngleKey, float | None]
AngleWindow = list[AngleVector]

REGION_ANGLES: dict[BodyRegion, list[AngleKey]] = {
    BodyRegion.TORSO: [],
    BodyRegion.LEFT_SHOULDER: [AngleKey.L_SHOULDER_ABD],
    BodyRegion.LEFT_ELBOW: [AngleKey.L_ELBOW],
    BodyRegion.LEFT_WRIST: [],
    BodyRegion.RIGHT_SHOULDER: [AngleKey.R_SHOULDER_ABD],
    BodyRegion.RIGHT_ELBOW: [AngleKey.R_ELBOW],
    BodyRegion.RIGHT_WRIST: [],
    BodyRegion.LEFT_HIP: [AngleKey.L_HIP],
    BodyRegion.LEFT_KNEE: [AngleKey.L_KNEE],
    BodyRegion.LEFT_ANKLE: [AngleKey.L_ANKLE],
    BodyRegion.RIGHT_HIP: [AngleKey.R_HIP],
    BodyRegion.RIGHT_KNEE: [AngleKey.R_KNEE],
    BodyRegion.RIGHT_ANKLE: [AngleKey.R_ANKLE],
}


def angle_keys_for_regions(regions: Iterable[BodyRegion]) -> set[AngleKey]:
    keys: set[AngleKey] = set()
    for region in regions:
        keys.update(REGION_ANGLES[region])
    return keys


def mask_angles(angles: AngleVector, active: set[AngleKey]) -> AngleVector:
    return {key: (angles.get(key) if key in active else None) for key in AngleKey}


def default_focus_angle_keys() -> set[AngleKey]:
    return angle_keys_for_regions(MEASURABLE_REGIONS)


assert angle_keys_for_regions(MEASURABLE_REGIONS) == set(AngleKey)


def valid_values(values: Iterable[float | None]) -> list[float]:
    return [v for v in values if v is not None]


def reduce_joints(
    frames: list[AngleVector], fn: Callable[[list[float]], float]
) -> AngleVector:
    """Per-joint reduction"""
    out: AngleVector = {}
    for joint in AngleKey:
        vals = valid_values(frame.get(joint) for frame in frames)
        out[joint] = float(fn(vals)) if vals else None
    return out


def joint_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float | None:
    ba = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    bc = np.asarray(c, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    # Coincident points -> angle undefined. Return None
    if denom == 0.0:
        return None
    cos = float(np.dot(ba, bc) / denom)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


class FeatureExtractor:
    def __init__(self, vis_floor: float = VIS_FLOOR) -> None:
        self.vis_floor = vis_floor

    def to_angles(
        self,
        lm: PoseLandmarks,
        keys: Iterable[AngleKey] | None = None,
    ) -> AngleVector:
        """Extract joint angles. If ``keys`` is set, only those joints are computed."""
        active = set(keys) if keys is not None else None
        angles: AngleVector = {}
        for key, (a, b, c) in ANGLE_TRIPLETS.items():
            if active is not None and key not in active:
                angles[key] = None
                continue
            idx = (int(a), int(b), int(c))
            if np.any(lm.visibility[list(idx)] < self.vis_floor):
                angles[key] = None
                continue
            angles[key] = joint_angle(lm.xyz[idx[0]], lm.xyz[idx[1]], lm.xyz[idx[2]])
        return angles
