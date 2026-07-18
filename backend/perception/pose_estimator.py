import pathlib, urllib.request

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

from ..pose_types import PoseLandmarks

INITIAL_TIMESTAMP_MS = -1
# Download the pose landmarker model if it doesn't exist
MODEL_URL = (
  "https://storage.googleapis.com/mediapipe-models/"
  "pose_landmarker/pose_landmarker_lite/"
  "float16/latest/pose_landmarker_lite.task"
)
MODEL_PATH = pathlib.Path(__file__).parent / "pose_landmarker_lite.task"

if not MODEL_PATH.exists():
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

class PoseEstimator:
    def __init__(self):
        # Initialize the pose landmarker with the model
        opts = PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5
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
        else:
            return None
    
    def close(self):
        self.detector.close()
