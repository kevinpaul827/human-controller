"""Constants for drawing the live session pose overlay."""

from backend.matching_engine.core.angles import ANGLE_TRIPLETS, AngleKey
from backend.pose_types import BlazePose33

# BlazePose landmark enum pairs to connect with skeleton lines, for example
# `(BlazePose33.NOSE, BlazePose33.L_EYE_INNER)` draws a line from the nose
# to the left inner eye landmark.
POSE_CONNECTIONS = [
    (BlazePose33.NOSE, BlazePose33.L_EYE_INNER),
    (BlazePose33.L_EYE_INNER, BlazePose33.L_EYE),
    (BlazePose33.L_EYE, BlazePose33.L_EYE_OUTER),
    (BlazePose33.L_EYE_OUTER, BlazePose33.L_EAR),
    (BlazePose33.NOSE, BlazePose33.R_EYE_INNER),
    (BlazePose33.R_EYE_INNER, BlazePose33.R_EYE),
    (BlazePose33.R_EYE, BlazePose33.R_EYE_OUTER),
    (BlazePose33.R_EYE_OUTER, BlazePose33.R_EAR),
    (BlazePose33.MOUTH_L, BlazePose33.MOUTH_R),
    (BlazePose33.L_SHOULDER, BlazePose33.R_SHOULDER),
    (BlazePose33.L_SHOULDER, BlazePose33.L_ELBOW),
    (BlazePose33.L_ELBOW, BlazePose33.L_WRIST),
    (BlazePose33.L_WRIST, BlazePose33.L_PINKY),
    (BlazePose33.L_WRIST, BlazePose33.L_INDEX),
    (BlazePose33.L_WRIST, BlazePose33.L_THUMB),
    (BlazePose33.R_SHOULDER, BlazePose33.R_ELBOW),
    (BlazePose33.R_ELBOW, BlazePose33.R_WRIST),
    (BlazePose33.R_WRIST, BlazePose33.R_PINKY),
    (BlazePose33.R_WRIST, BlazePose33.R_INDEX),
    (BlazePose33.R_WRIST, BlazePose33.R_THUMB),
    (BlazePose33.L_SHOULDER, BlazePose33.L_HIP),
    (BlazePose33.R_SHOULDER, BlazePose33.R_HIP),
    (BlazePose33.L_HIP, BlazePose33.R_HIP),
    (BlazePose33.L_HIP, BlazePose33.L_KNEE),
    (BlazePose33.L_KNEE, BlazePose33.L_ANKLE),
    (BlazePose33.L_ANKLE, BlazePose33.L_HEEL),
    (BlazePose33.L_HEEL, BlazePose33.L_FOOT_INDEX),
    (BlazePose33.R_HIP, BlazePose33.R_KNEE),
    (BlazePose33.R_KNEE, BlazePose33.R_ANKLE),
    (BlazePose33.R_ANKLE, BlazePose33.R_HEEL),
    (BlazePose33.R_HEEL, BlazePose33.R_FOOT_INDEX),
]

# Ignore landmarks below this confidence so weak detections do not clutter the overlay.
MIN_VISIBILITY = 0.35


def landmarks_for_angle_joints(joint_names) -> set[BlazePose33]:
    landmarks: set[BlazePose33] = set()
    for joint_name in joint_names:
        try:
            joint = AngleKey(joint_name)
        except ValueError:
            continue
        landmarks.update(ANGLE_TRIPLETS[joint])
    return landmarks


def connections_for_angle_joints(
    joint_names,
) -> set[tuple[BlazePose33, BlazePose33]]:
    connections: set[tuple[BlazePose33, BlazePose33]] = set()
    for joint_name in joint_names:
        try:
            joint = AngleKey(joint_name)
        except ValueError:
            continue
        first, centre, last = ANGLE_TRIPLETS[joint]
        connections.add((first, centre))
        connections.add((centre, last))
    return connections
