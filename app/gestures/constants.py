"""Persistence and matching policy for user-created gestures."""

GESTURES_DIR_ENV = "HUMAN_CONTROLLER_GESTURES_DIR"
PROJECT_ROOT_ENV = "HUMAN_CONTROLLER_PROJECT_ROOT"

# A matcher score uses 0.0–1.0. The motion window holds recent pose frames.
DEFAULT_MATCH_THRESHOLD = 0.75
MOTION_WINDOW_FRAMES = 150
MOTION_MIN_TEMPLATE_RANGE_DEG = 15.0
