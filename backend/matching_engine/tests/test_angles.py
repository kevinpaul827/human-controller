"""Simple tests for joint angle calculations and feature extraction."""

import numpy as np
import pytest

from backend.matching_engine.core.angles import (
    ANGLE_TRIPLETS,
    AngleKey,
    FeatureExtractor,
    joint_angle,
)
from backend.pose_types import BlazePose33, PoseLandmarks


def test_joint_angle_right_angle():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 0.0, 0.0])
    c = np.array([0.0, 1.0, 0.0])
    assert joint_angle(a, b, c) == pytest.approx(90.0)


def test_joint_angle_straight_line():
    a = np.array([-1.0, 0.0, 0.0])
    b = np.array([0.0, 0.0, 0.0])
    c = np.array([1.0, 0.0, 0.0])
    assert joint_angle(a, b, c) == pytest.approx(180.0)


def test_joint_angle_coincident_points():
    # Undefined angle -> None (masked), distinct from a valid 0 degrees.
    a = b = c = np.zeros(3)
    assert joint_angle(a, b, c) is None


def _straight_arm_landmarks() -> PoseLandmarks:
    lm = PoseLandmarks.empty()
    lm.visibility[:] = 1.0
    # all points colinear -> angle 180.
    lm.xyz[BlazePose33.L_SHOULDER] = [0.0, 0.0, 0.0]
    lm.xyz[BlazePose33.L_ELBOW] = [0.0, -1.0, 0.0]
    lm.xyz[BlazePose33.L_WRIST] = [0.0, -2.0, 0.0]
    return lm


def test_feature_extractor_straight_arm():
    lm = _straight_arm_landmarks()
    angles = FeatureExtractor().to_angles(lm)
    assert angles[AngleKey.L_ELBOW] == pytest.approx(180.0)


def test_feature_extractor_low_visibility():
    lm = _straight_arm_landmarks()
    fe = FeatureExtractor(vis_floor=0.5)
    lm.visibility[BlazePose33.L_WRIST] = 0.1  # below floor
    angles = fe.to_angles(lm)
    assert angles[AngleKey.L_ELBOW] is None

