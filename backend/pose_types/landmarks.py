"""Application pose-keypoint data structures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import numpy as np

MEDIAPIPE_NUM_LANDMARKS = 33


class PoseKeypoint(IntEnum):
    """Keypoints used by gesture matching, stored in compact array order."""

    L_SHOULDER = 0
    R_SHOULDER = 1
    L_ELBOW = 2
    R_ELBOW = 3
    L_WRIST = 4
    R_WRIST = 5
    L_HIP = 6
    R_HIP = 7
    L_KNEE = 8
    R_KNEE = 9
    L_ANKLE = 10
    R_ANKLE = 11
    L_HEEL = 12
    R_HEEL = 13
    L_FOOT_INDEX = 14
    R_FOOT_INDEX = 15


NUM_LANDMARKS = len(PoseKeypoint)

# Source indices in MediaPipe's 33-landmark result. Face and finger points are
# discarded as soon as a detector result enters the application.
MEDIAPIPE_POSE_INDICES: tuple[int, ...] = (
    11,
    12,
    13,
    14,
    15,
    16,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
)


@dataclass
class PoseLandmarks:
    xyz: np.ndarray  # (16, 3)
    visibility: np.ndarray  # (16,) in [0, 1]

    def __post_init__(self) -> None:
        self.xyz = np.asarray(self.xyz, dtype=np.float64)
        self.visibility = np.asarray(self.visibility, dtype=np.float64)
        if self.xyz.shape != (NUM_LANDMARKS, 3):
            raise ValueError(
                f"xyz must have shape ({NUM_LANDMARKS}, 3), got {self.xyz.shape}"
            )
        if self.visibility.shape != (NUM_LANDMARKS,):
            raise ValueError(
                "visibility must have shape "
                f"({NUM_LANDMARKS},), got {self.visibility.shape}"
            )
        if not np.isfinite(self.xyz).all():
            raise ValueError("xyz values must be finite")
        if not np.isfinite(self.visibility).all():
            raise ValueError("visibility values must be finite")
        if np.any((self.visibility < 0.0) | (self.visibility > 1.0)):
            raise ValueError("visibility values must be between 0 and 1")

    # Allows for frames with no data.
    @classmethod
    def empty(cls) -> "PoseLandmarks":
        return cls(
            xyz=np.zeros((NUM_LANDMARKS, 3), dtype=np.float64),
            visibility=np.zeros(NUM_LANDMARKS, dtype=np.float64),
        )

    @classmethod
    def from_mediapipe(cls, xyz, visibility) -> "PoseLandmarks":
        """Build the compact application pose from a MediaPipe result."""
        source_xyz = np.asarray(xyz, dtype=np.float64)
        source_visibility = np.asarray(visibility, dtype=np.float64)
        if source_xyz.shape != (MEDIAPIPE_NUM_LANDMARKS, 3):
            raise ValueError(
                "MediaPipe xyz must have shape "
                f"({MEDIAPIPE_NUM_LANDMARKS}, 3), got {source_xyz.shape}"
            )
        if source_visibility.shape != (MEDIAPIPE_NUM_LANDMARKS,):
            raise ValueError(
                "MediaPipe visibility must have shape "
                f"({MEDIAPIPE_NUM_LANDMARKS},), got {source_visibility.shape}"
            )

        source_indices = list(MEDIAPIPE_POSE_INDICES)
        return cls(source_xyz[source_indices], source_visibility[source_indices])
