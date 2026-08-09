import math

import numpy as np
import pytest

from backend.pose_types import (
    BODY_CONNECTIONS,
    BODY_LANDMARKS,
    NUM_LANDMARKS,
    BodyRegion,
    PoseLandmarks,
    group_region_ids,
    parse_regions,
)


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
    assert len(BODY_LANDMARKS) == 16
    assert len(BODY_CONNECTIONS) == 16
    assert isinstance(BODY_LANDMARKS, tuple)
    assert isinstance(BODY_CONNECTIONS, tuple)


def test_region_parsing_and_group_lookup():
    assert parse_regions(["left_elbow", "invalid"]) == [BodyRegion.LEFT_ELBOW]
    assert group_region_ids("left_arm") == [
        BodyRegion.LEFT_SHOULDER,
        BodyRegion.LEFT_ELBOW,
        BodyRegion.LEFT_WRIST,
        BodyRegion.LEFT_HAND,
    ]
    assert group_region_ids("invalid") == []
