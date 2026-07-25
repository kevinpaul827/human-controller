

from backend.matching_engine.core.angles import ANGLE_TRIPLETS, AngleKey
from backend.pose_types import BlazePose33




BODY_LANDMARKS = {
    BlazePose33.L_SHOULDER,
    BlazePose33.R_SHOULDER,
    BlazePose33.L_ELBOW,
    BlazePose33.R_ELBOW,
    BlazePose33.L_WRIST,
    BlazePose33.R_WRIST,
    BlazePose33.L_HIP,
    BlazePose33.R_HIP,
    BlazePose33.L_KNEE,
    BlazePose33.R_KNEE,
    BlazePose33.L_ANKLE,
    BlazePose33.R_ANKLE,
    BlazePose33.L_HEEL,
    BlazePose33.R_HEEL,
    BlazePose33.L_FOOT_INDEX,
    BlazePose33.R_FOOT_INDEX,
}

POSE_CONNECTIONS = [
    (BlazePose33.L_SHOULDER, BlazePose33.R_SHOULDER),
    (BlazePose33.L_SHOULDER, BlazePose33.L_ELBOW),
    (BlazePose33.L_ELBOW, BlazePose33.L_WRIST),
    (BlazePose33.R_SHOULDER, BlazePose33.R_ELBOW),
    (BlazePose33.R_ELBOW, BlazePose33.R_WRIST),
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
