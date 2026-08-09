import math

import numpy as np
import pytest

from backend.pose_types import (
    BODY_CONNECTIONS,
    BODY_LANDMARKS,
    NUM_LANDMARKS,
    BodyRegion,
    PoseKeypoint,
    PoseLandmarks,
    group_region_ids,
    parse_regions,
)


REMOVED_KEYPOINT_NAMES = {
    "NOSE",
    "L_EYE_INNER",
    "L_EYE",
    "L_EYE_OUTER",
    "R_EYE_INNER",
    "R_EYE",
    "R_EYE_OUTER",
    "L_EAR",
    "R_EAR",
    "MOUTH_L",
    "MOUTH_R",
    "L_PINKY",
    "R_PINKY",
    "L_INDEX",
    "R_INDEX",
    "L_THUMB",
    "R_THUMB",
}


def test_landmarks_require_finite_coordinates():
    xyz = np.zeros((NUM_LANDMARKS, 3))
    xyz[0, 0] = math.nan

    with pytest.raises(ValueError, match="xyz values"):
        PoseLandmarks(xyz, np.ones(NUM_LANDMARKS))


@pytest.mark.parametrize("visibility", [-0.1, 1.1, math.nan])
def test_landmarks_reject_invalid_visibility(visibility):
    values = np.ones(NUM_LANDMARKS)
    values[0] = visibility

    with pytest.raises(ValueError, match="visibility values"):
        PoseLandmarks(np.zeros((NUM_LANDMARKS, 3)), values)


def test_default_skeleton_contract_is_stable():
    assert NUM_LANDMARKS == 16
    assert len(BODY_LANDMARKS) == 16
    assert len(BODY_CONNECTIONS) == 16
    assert BODY_LANDMARKS == tuple(range(NUM_LANDMARKS))
    assert isinstance(BODY_LANDMARKS, tuple)
    assert isinstance(BODY_CONNECTIONS, tuple)


def test_pose_keypoints_exclude_face_and_fingers():
    assert REMOVED_KEYPOINT_NAMES.isdisjoint(PoseKeypoint.__members__)


def test_mediapipe_pose_is_compacted_to_supported_keypoints():
    source_xyz = np.arange(33 * 3, dtype=np.float64).reshape(33, 3)
    source_visibility = np.linspace(0.0, 1.0, 33)

    pose = PoseLandmarks.from_mediapipe(source_xyz, source_visibility)

    source_indices = [11, 12, 13, 14, 15, 16, *range(23, 33)]
    np.testing.assert_array_equal(pose.xyz, source_xyz[source_indices])
    np.testing.assert_array_equal(
        pose.visibility,
        source_visibility[source_indices],
    )


def test_region_parsing_and_group_lookup():
    assert parse_regions(["left_elbow", "invalid"]) == [BodyRegion.LEFT_ELBOW]
    assert group_region_ids("left_arm") == [
        BodyRegion.LEFT_SHOULDER,
        BodyRegion.LEFT_ELBOW,
        BodyRegion.LEFT_WRIST,
    ]
    assert group_region_ids("invalid") == []
