"""Tests for the v2 DTW motion matcher and motion template building."""

from typing import List, Optional

import pytest

from backend.matching_engine.core.angles import AngleKey, AngleVector
from backend.matching_engine.core.types import GestureTemplate
from backend.matching_engine.matching.motion_matcher import (
    MotionMatcher,
    dtw_distance,
)
from backend.matching_engine.templates.builder import TemplateBuilder

ELBOW, SHOULDER = AngleKey.L_ELBOW, AngleKey.L_SHOULDER_ABD


def _window(elbow: List[Optional[float]]) -> List[AngleVector]:
    return [{ELBOW: v} for v in elbow]


def _ramp(start: float, stop: float, n: int) -> List[Optional[float]]:
    step = (stop - start) / (n - 1)
    return [start + step * i for i in range(n)]


def _motion_template(elbow: List[float], name: str = "raise") -> GestureTemplate:
    return GestureTemplate(
        name=name,
        active_joints=[ELBOW],
        trajectory=[{ELBOW: v} for v in elbow],
        fps=30,
    )


# --- dtw_distance --------------------------------------------------------


def test_identical_sequences_zero_distance():
    seq = _window(_ramp(0.0, 90.0, 10))
    assert dtw_distance(seq, seq, [ELBOW]) == pytest.approx(0.0)


def test_time_warp_invariance():
    """A slower trace of the same movement should align near-perfectly."""
    fast = _window(_ramp(0.0, 90.0, 10))
    # Same path, performed at half speed (each frame duplicated).
    slow = _window([v for v in _ramp(0.0, 90.0, 10) for _ in range(2)])
    assert dtw_distance(fast, slow, [ELBOW]) == pytest.approx(0.0, abs=1e-6)


def test_different_shape_has_positive_distance():
    up = _window(_ramp(0.0, 90.0, 10))
    down = _window(_ramp(90.0, 0.0, 10))
    assert dtw_distance(up, down, [ELBOW]) > 0.0


def test_empty_sequence_is_infinite():
    assert dtw_distance([], _window([1.0]), [ELBOW]) == float("inf")


def test_no_comparable_joints_uses_miss_penalty():
    a = _window([10.0, 20.0])
    b = [{SHOULDER: 10.0}, {SHOULDER: 20.0}]  # different joint entirely
    # All alignments cost the miss penalty -> distance equals it.
    assert dtw_distance(a, b, [ELBOW, SHOULDER]) == pytest.approx(180.0)


def test_band_constraint_still_matches_aligned_sequences():
    seq = _window(_ramp(0.0, 90.0, 12))
    assert dtw_distance(seq, seq, [ELBOW], band=2) == pytest.approx(0.0)


def test_invalid_dtw_configuration_is_rejected():
    sequence = _window([1.0])
    with pytest.raises(ValueError, match="band"):
        dtw_distance(sequence, sequence, [ELBOW], band=1.5)
    with pytest.raises(ValueError, match="step pattern"):
        dtw_distance(sequence, sequence, [ELBOW], step_pattern="bogus")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"band": -1}, "band"),
        ({"default_tolerance_deg": 0.0}, "default_tolerance_deg"),
        ({"step_pattern": "bogus"}, "step pattern"),
        ({"min_amplitude_ratio": 1.1}, "min_amplitude_ratio"),
        ({"coverage_tol_deg": -1.0}, "coverage_tol_deg"),
    ],
)
def test_invalid_matcher_configuration_is_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        MotionMatcher(**kwargs)


def test_default_step_pattern_is_slope_constrained():
    assert MotionMatcher().step_pattern == "symmetricP1"


def test_slope_constraint_rejects_extreme_speed_ratio():
    short = _window(_ramp(0.0, 90.0, 5))
    long = _window(_ramp(0.0, 90.0, 30))  # ratio 6 > 2
    assert dtw_distance(short, long, [ELBOW]) == float("inf")


def test_plain_pattern_allows_extreme_speed_ratio():
    short = _window(_ramp(0.0, 90.0, 5))
    long = _window(_ramp(0.0, 90.0, 30))
    d = dtw_distance(short, long, [ELBOW], step_pattern="symmetric1")
    assert d < float("inf")


def test_weighted_normalization_is_path_independent():
    seq = _window(_ramp(0.0, 90.0, 15))
    assert dtw_distance(seq, seq, [ELBOW], step_pattern="symmetric2") == pytest.approx(0.0)


def test_open_begin_finds_gesture_in_padded_window():
    template = _motion_template([float(v) for v in _ramp(0.0, 90.0, 12)])
    mm = MotionMatcher(step_pattern="symmetric2", open_begin=True)
    # leading idle frames + the gesture; free start should skip the padding.
    window = _window([0.0] * 40 + list(_ramp(0.0, 90.0, 12)))
    assert mm.score(window, template) > 0.9


def test_open_begin_speed_invariant_for_slow_performance():
    template = _motion_template([float(v) for v in _ramp(0.0, 90.0, 12)])
    mm = MotionMatcher(step_pattern="symmetric2", open_begin=True)
    slow = _window([v for v in _ramp(0.0, 90.0, 12) for _ in range(8)])  # 8x slower
    assert mm.score(slow, template) > 0.9


def test_amplitude_gate_rejects_small_movement():
    template = _motion_template([float(v) for v in _ramp(0.0, 90.0, 12)])
    mm = MotionMatcher(step_pattern="symmetric2", open_begin=True, min_amplitude_ratio=0.5)
    small = _window([45.0 + (i % 3) for i in range(40)])  # ~2 deg wiggle
    full = _window([0.0] * 20 + list(_ramp(0.0, 90.0, 12)))
    assert mm.score(small, template) == 0.0
    assert mm.score(full, template) > 0.9


def test_end_pose_gate_rejects_incomplete_movement():
    template = _motion_template([float(v) for v in _ramp(0.0, 90.0, 12)])
    mm = MotionMatcher(step_pattern="symmetric2", open_begin=True, end_pose_tol_deg=15.0)
    complete = _window(list(_ramp(0.0, 90.0, 12)) + [90.0] * 30)
    stopped_short = _window(list(_ramp(0.0, 60.0, 12)) + [60.0] * 30)  # ends 30 deg short
    assert mm.score(complete, template) > 0.9
    assert mm.score(stopped_short, template) == 0.0


def test_coverage_gate_rejects_partial_motion_ending_at_end_pose():
    template = _motion_template([float(v) for v in _ramp(0.0, 90.0, 12)])
    matcher = MotionMatcher(
        step_pattern="symmetric2",
        open_begin=True,
        end_pose_tol_deg=15.0,
        coverage_tol_deg=20.0,
    )
    partial = _window(
        [30.0] * 10 + list(_ramp(30.0, 90.0, 8)) + [90.0] * 20
    )
    full = _window(
        [0.0] * 10 + list(_ramp(0.0, 90.0, 12)) + [90.0] * 20
    )

    assert matcher.score(partial, template) == 0.0
    assert matcher.score(full, template) > 0.9


def test_coverage_gate_requires_template_order():
    template = _motion_template([0.0, 30.0, 60.0, 90.0, 60.0, 30.0])
    matcher = MotionMatcher(
        step_pattern="symmetric2",
        open_begin=True,
        coverage_tol_deg=10.0,
    )
    up_only = _window([0.0, 10.0, 20.0, 30.0] + [30.0] * 10)
    full = _window(
        [0.0, 30.0, 60.0, 90.0, 60.0, 30.0] + [30.0] * 5
    )

    assert matcher.score(up_only, template) == 0.0
    assert matcher.score(full, template) > 0.9


def test_template_range_gate_rejects_nearly_static_motion_template():
    template = _motion_template([45.0, 47.0, 44.0, 46.0, 45.0])
    matcher = MotionMatcher(
        step_pattern="symmetric2",
        open_begin=True,
        min_template_range_deg=15.0,
    )

    assert matcher.score(_window([45.0] * 40), template) == 0.0


# --- MotionMatcher.score -------------------------------------------------


def test_perfect_trace_scores_one():
    path = _ramp(0.0, 90.0, 12)
    template = _motion_template([float(v) for v in path])
    assert MotionMatcher().score(_window(path), template) == pytest.approx(1.0)


def test_speed_invariant_score_stays_high():
    path = _ramp(0.0, 90.0, 12)
    template = _motion_template([float(v) for v in path])
    slow = _window([v for v in path for _ in range(2)])
    assert MotionMatcher().score(slow, template) > 0.95


def test_wrong_movement_scores_lower_than_right_one():
    path = _ramp(0.0, 90.0, 12)
    template = _motion_template([float(v) for v in path])
    right = MotionMatcher().score(_window(path), template)
    wrong = MotionMatcher().score(_window(_ramp(90.0, 0.0, 12)), template)
    assert wrong < right
    assert 0.0 <= wrong <= 1.0


def test_empty_window_scores_zero():
    template = _motion_template(_ramp(0.0, 90.0, 5))  # type: ignore[arg-type]
    assert MotionMatcher().score([], template) == 0.0


def test_empty_trajectory_scores_zero():
    template = GestureTemplate(name="x", active_joints=[ELBOW])
    assert MotionMatcher().score(_window([1.0, 2.0]), template) == 0.0


# --- MotionMatcher.best_match --------------------------------------------


def test_best_match_picks_closest_trajectory():
    up = _motion_template([float(v) for v in _ramp(0.0, 90.0, 12)], name="up")
    up.gesture_id = "up"
    down = _motion_template([float(v) for v in _ramp(90.0, 0.0, 12)], name="down")
    down.gesture_id = "down"

    result = MotionMatcher().best_match(
        _window(_ramp(0.0, 90.0, 12)), [down, up], timestamp=1.0
    )
    assert result is not None
    assert result.gesture_id == "up"
    assert result.timestamp == 1.0


def test_best_match_empty_returns_none():
    assert MotionMatcher().best_match(_window([1.0]), []) is None


# --- TemplateBuilder motion mode -----------------------------------------


def test_build_motion_produces_normalised_trajectory():
    builder = TemplateBuilder(motion_trajectory_frames=16)
    rep1 = _window(_ramp(0.0, 90.0, 20))
    rep2 = _window(_ramp(0.0, 90.0, 30))  # same movement, different length
    template = builder.build_motion([rep1, rep2], name="arm raise")

    assert len(template.trajectory) == 16
    assert ELBOW in template.active_joints
    # Trajectory should be monotonically increasing like the underlying ramp.
    vals = [f[ELBOW] for f in template.trajectory]
    assert vals == sorted(vals)


def test_built_motion_template_matches_its_own_reps():
    builder = TemplateBuilder(motion_trajectory_frames=16)
    rep = _window(_ramp(0.0, 90.0, 24))
    template = builder.build_motion([rep, rep], name="arm raise")
    assert MotionMatcher().score(rep, template) > 0.9


def test_motion_template_round_trips_through_dict():
    template = _motion_template([float(v) for v in _ramp(0.0, 90.0, 8)])
    restored = GestureTemplate.from_dict(template.to_dict())
    assert restored.trajectory == template.trajectory
    assert restored.active_joints == template.active_joints
