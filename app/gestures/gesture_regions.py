from __future__ import annotations

UPPER_BODY_JOINTS = {
    "L_ELBOW",
    "R_ELBOW",
    "L_SHOULDER_ABD",
    "R_SHOULDER_ABD",
}

LOWER_BODY_JOINTS = {
    "L_HIP",
    "R_HIP",
    "L_KNEE",
    "R_KNEE",
    "L_ANKLE",
    "R_ANKLE",
}


def infer_gesture_regions(active_joints: list[str]) -> list[str]:
    """Infer coarse body regions for saved gesture metadata."""
    regions: list[str] = []
    joint_set = set(active_joints)

    if joint_set & UPPER_BODY_JOINTS:
        regions.append("upper_body")

    if joint_set & LOWER_BODY_JOINTS:
        regions.append("lower_body")

    return regions
