import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)

from ..pose_types import PoseLandmarks
from .models import DEFAULT_POSE_MODEL, normalize_pose_model, pose_model_path

INITIAL_TIMESTAMP_MS = -1


class PoseEstimator:
    def __init__(self, model=DEFAULT_POSE_MODEL):
        self.model = normalize_pose_model(model)
        model_path = pose_model_path(self.model)
        if not model_path.is_file():
            raise FileNotFoundError(f"Pose model asset is missing: {model_path}")
        opts = PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.detector = PoseLandmarker.create_from_options(opts)
        self.last_timestamp_ms = INITIAL_TIMESTAMP_MS

    def estimate_pose(self, frame, timestamp_ms) -> PoseLandmarks | None:
        timestamp_ms = max(timestamp_ms, self.last_timestamp_ms + 1)
        self.last_timestamp_ms = timestamp_ms

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame, dtype=np.uint8)

        mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self.detector.detect_for_video(mp_frame, timestamp_ms)

        if result.pose_landmarks:
            xyz_list = []
            vis_list = []

            for lm in result.pose_landmarks[0]:
                xyz_list.append([lm.x, lm.y, lm.z])
                vis_list.append(lm.visibility)

            classed_plm = PoseLandmarks(xyz_list, vis_list)
            return classed_plm
        return None

    def close(self):
        detector = self.detector
        if detector is None:
            return
        self.detector = None
        detector.close()
