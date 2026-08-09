import pytest

from backend.matching_engine.core.angles import AngleKey
from backend.matching_engine.templates.builder import TemplateBuilder


def _rep(elbow_start, elbow_end, shoulder=30.0, n=20, plateau=6):
    frames = []
    ramp = n - plateau
    for index in range(n):
        if index < ramp:
            fraction = index / (ramp - 1)
            elbow = elbow_start + (elbow_end - elbow_start) * fraction
        else:
            elbow = elbow_end
        frames.append(
            {
                AngleKey.L_ELBOW: elbow,
                AngleKey.L_SHOULDER_ABD: shoulder,
            }
        )
    return frames


def test_active_joint_detection_picks_moving_joint():
    builder = TemplateBuilder()
    active = builder.detect_active_joints(
        [_rep(90.0, 170.0), _rep(92.0, 172.0)]
    )

    assert AngleKey.L_ELBOW in active
    assert AngleKey.L_SHOULDER_ABD not in active


def test_build_motion_produces_normalized_trajectory():
    builder = TemplateBuilder(motion_trajectory_frames=24)
    template = builder.build_motion(
        [_rep(90.0, 170.0), _rep(92.0, 172.0)],
        name="arm raise",
    )

    assert len(template.trajectory) == 24
    assert AngleKey.L_ELBOW in template.active_joints


@pytest.mark.parametrize(
    "kwargs",
    [
        {"motion_trajectory_frames": 1},
        {"min_active_range_deg": -1.0},
    ],
)
def test_invalid_builder_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        TemplateBuilder(**kwargs)


def test_empty_reps_are_rejected():
    with pytest.raises(ValueError):
        TemplateBuilder().build_motion([], name="arm raise")


def test_empty_repetition_is_rejected():
    with pytest.raises(ValueError, match="at least one frame"):
        TemplateBuilder().build_motion([[]], name="arm raise")


def test_non_finite_repetition_is_rejected():
    with pytest.raises(ValueError, match="finite"):
        TemplateBuilder().build_motion(
            [[{AngleKey.L_ELBOW: float("nan")}]],
            name="arm raise",
        )
