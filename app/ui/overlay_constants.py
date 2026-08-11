"""overlay_constants.py

Constants for drawing the live session pose overlay.
"""
from backend.matching_engine.core.angles import ANGLE_TRIPLETS, AngleKey
from backend.pose_types import BODY_CONNECTIONS, PoseKeypoint

# The overlay and matcher share the same compact body-only skeleton.
POSE_CONNECTIONS = BODY_CONNECTIONS

# Ignore landmarks below this confidence so weak detections do not clutter the overlay.
MIN_VISIBILITY = 0.35

# Alpha-beta tracker gains: alpha corrects position and beta corrects velocity.
# Higher gains follow detections more closely but smooth less.
# Reference: https://kalmanfilter.net/alphabeta.html
POINT_RADIUS = 4
LINE_WIDTH = 3
POSE_TRACKER_ALPHA = 0.55
POSE_TRACKER_BETA = 0.08
# Durations in milliseconds. Cap extrapolation briefly; reset after a stale gap.
MAX_POSE_PROJECTION_MS = 33
POSE_TRACKER_RESET_GAP_MS = 250

def landmarks_for_angle_joints(joint_names) -> set[PoseKeypoint]:
    landmarks: set[PoseKeypoint] = set()
    for joint_name in joint_names:
        try:
            joint = AngleKey(joint_name)
        except ValueError:
            continue
        landmarks.update(ANGLE_TRIPLETS[joint])
    return landmarks


def connections_for_angle_joints(
    joint_names,
) -> set[tuple[PoseKeypoint, PoseKeypoint]]:
    connections: set[tuple[PoseKeypoint, PoseKeypoint]] = set()
    for joint_name in joint_names:
        try:
            joint = AngleKey(joint_name)
        except ValueError:
            continue
        first, centre, last = ANGLE_TRIPLETS[joint]
        connections.add((first, centre))
        connections.add((centre, last))
    return connections
