"""Tests for TemplateBuilder (active-joint detection and auto-threshold)."""

import pytest

from backend.matching_engine.core.angles import AngleKey
from backend.matching_engine.templates.builder import TemplateBuilder


def _rep(elbow_start, elbow_end, shoulder=30.0, n=20, plateau=6):
    frames = []
    ramp = n - plateau
    for i in range(n):
        if i < ramp:
            frac = i / (ramp - 1)
            elbow = elbow_start + (elbow_end - elbow_start) * frac
        else:
            elbow = elbow_end
        frames.append({AngleKey.L_ELBOW: elbow, AngleKey.L_SHOULDER_ABD: shoulder})
    return frames


def test_active_joint_detection_picks_moving_joint():
    builder = TemplateBuilder()
    reps = [_rep(90.0, 170.0), _rep(92.0, 172.0)]
    active = builder.detect_active_joints(reps)
    assert AngleKey.L_ELBOW in active
    # Shoulder barely moves -> not active.
    assert AngleKey.L_SHOULDER_ABD not in active


def test_build_target_is_mean_end_state():
    builder = TemplateBuilder()
    reps = [_rep(90.0, 170.0), _rep(90.0, 180.0)]
    template = builder.build(reps, name="arm raise", mode="state")
    assert template.type == "state"
    assert AngleKey.L_ELBOW in template.target_angles
    # End-state averaged over the last frames of both reps -> ~175.
    assert template.target_angles[AngleKey.L_ELBOW] == pytest.approx(175.0, abs=2.0)


def test_auto_threshold_has_floor():
    builder = TemplateBuilder(min_tolerance_deg=5.0)
    # Identical reps -> zero variance -> tolerance must fall back to the floor.
    reps = [_rep(90.0, 170.0), _rep(90.0, 170.0)]
    template = builder.build(reps, name="arm raise", mode="state")
    assert template.tolerance_deg[AngleKey.L_ELBOW] == pytest.approx(5.0)


def test_auto_threshold_scales_with_variance():
    builder = TemplateBuilder(tolerance_k=2.0, min_tolerance_deg=1.0)
    reps = [_rep(90.0, 150.0), _rep(90.0, 190.0)]  # end-state std = 20
    template = builder.build(reps, name="arm raise", mode="state")
    assert template.tolerance_deg[AngleKey.L_ELBOW] == pytest.approx(40.0, abs=2.0)


def test_motion_mode_not_supported_in_v1():
    with pytest.raises(NotImplementedError):
        TemplateBuilder().build([_rep(90.0, 170.0)], name="arm raise", mode="motion")


def test_empty_reps_raises():
    with pytest.raises(ValueError):
        TemplateBuilder().build([], name="arm raise", mode="state")
