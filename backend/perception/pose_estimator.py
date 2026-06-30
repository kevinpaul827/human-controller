import urllib.request, pathlib
import mediapipe as mp
import cv2
from ..pose_types import connections_for_regions, landmarks_for_regions, parse_regions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

GREEN = (0, 255, 0)
RED = (0, 0, 255)
QUIT_KEY = ord('q')

# Download the pose landmarker model if it doesn't exist
MODEL_URL = (
  "https://storage.googleapis.com/mediapipe-models/"
  "pose_landmarker/pose_landmarker_lite/"
  "float16/latest/pose_landmarker_lite.task"
)
MODEL_PATH = pathlib.Path(__file__).parent / "pose_landmarker_lite.task"

if not MODEL_PATH.exists():
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


DEFAULT_FOCUS: list[str] | None = None

opts = PoseLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
    running_mode=RunningMode.VIDEO,
    min_pose_detection_confidence=0.8,
    min_tracking_confidence=0.8
)

detector = PoseLandmarker.create_from_options(opts)

# Function to process a single frame and return the pose landmarks
def estimate_pose(frame, detector, timestamp_ms) -> PoseLandmarks | None:
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    result = detector.detect_for_video(mp_frame, timestamp_ms)

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
    

# Start capturing video from the camera and process each frame
feed = cv2.VideoCapture(0)
while feed.isOpened():
    ret, frame = feed.read()
    if not ret:
        break

    ts = int(feed.get(cv2.CAP_PROP_POS_MSEC))
    pose_landmarks = estimate_pose(frame, detector, ts)

    if pose_landmarks:
        h, w = frame.shape[:2]
        regions = parse_regions(DEFAULT_FOCUS)
        draw_landmarks = set(landmarks_for_regions(regions))
        draw_connections = connections_for_regions(regions)
        pts = [
            (int(pose_landmarks.xyz[i][0] * w), int(pose_landmarks.xyz[i][1] * h))
            for i in range(len(pose_landmarks.xyz))
        ]

        for a, b in draw_connections:
            cv2.line(frame, pts[a], pts[b], GREEN, 2)

        for i in draw_landmarks:
            cx, cy = pts[i]
            cv2.circle(frame, (cx, cy), 5, RED, -1)

    cv2.imshow('Camera Feed', frame)
    if cv2.waitKey(10) & 0xFF == QUIT_KEY:
        break

feed.release()
cv2.destroyAllWindows()