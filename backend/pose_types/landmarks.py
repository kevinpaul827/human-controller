"""BlazePose result data structure"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import numpy as np

NUM_LANDMARKS = 33


# https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker
class BlazePose33(IntEnum):
    NOSE = 0
    L_EYE_INNER = 1
    L_EYE = 2
    L_EYE_OUTER = 3
    R_EYE_INNER = 4
    R_EYE = 5
    R_EYE_OUTER = 6
    L_EAR = 7
    R_EAR = 8
    MOUTH_L = 9
    MOUTH_R = 10
    L_SHOULDER = 11
    R_SHOULDER = 12
    L_ELBOW = 13
    R_ELBOW = 14
    L_WRIST = 15
    R_WRIST = 16
    L_PINKY = 17
    R_PINKY = 18
    L_INDEX = 19
    R_INDEX = 20
    L_THUMB = 21
    R_THUMB = 22
    L_HIP = 23
    R_HIP = 24
    L_KNEE = 25
    R_KNEE = 26
    L_ANKLE = 27
    R_ANKLE = 28
    L_HEEL = 29
    R_HEEL = 30
    L_FOOT_INDEX = 31
    R_FOOT_INDEX = 32


@dataclass
class PoseLandmarks:
    xyz: np.ndarray  # (33, 3)
    visibility: np.ndarray  # (33,) in [0, 1]

    def __post_init__(self) -> None:
        self.xyz = np.asarray(self.xyz, dtype=np.float64)
        self.visibility = np.asarray(self.visibility, dtype=np.float64)
        if self.xyz.shape != (NUM_LANDMARKS, 3):
            raise ValueError(f"xyz must have shape ({NUM_LANDMARKS}, 3), got {self.xyz.shape}")
        if self.visibility.shape != (NUM_LANDMARKS,):
            raise ValueError(
                f"visibility must have shape ({NUM_LANDMARKS},), got {self.visibility.shape}"
            )
        if not np.isfinite(self.xyz).all():
            raise ValueError("xyz values must be finite")
        if not np.isfinite(self.visibility).all():
            raise ValueError("visibility values must be finite")
        if np.any((self.visibility < 0.0) | (self.visibility > 1.0)):
            raise ValueError("visibility values must be between 0 and 1")

    #allows for frames with no data
    @classmethod
    def empty(cls) -> "PoseLandmarks":
        return cls(
            xyz=np.zeros((NUM_LANDMARKS, 3), dtype=np.float64),
            visibility=np.zeros(NUM_LANDMARKS, dtype=np.float64),
        )
