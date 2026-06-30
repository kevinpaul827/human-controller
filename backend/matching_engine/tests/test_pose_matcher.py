"""Tests for v1 state matcher."""

import pytest

from backend.matching_engine.core.angles import AngleKey
from backend.matching_engine.core.types import GestureTemplate
from backend.matching_engine.matching.pose_matcher import PoseMatcher, state_score

ELBOW, SHOULDER = AngleKey.L_ELBOW, AngleKey.L_SHOULDER_ABD


def _template() -> GestureTemplate:
    return GestureTemplate(
        type="state",
        active_joints=[ELBOW, SHOULDER],
        target_angles={ELBOW: 170.0, SHOULDER: 90.0},
        tolerance_deg={ELBOW: 20.0, SHOULDER: 10.0},
        gesture_id="g1",
        name="arm raise",
    )


def _score(current: dict[AngleKey, float]) -> float:
    t = _template()
    return state_score(current, t.target_angles, t.tolerance_deg)


def test_perfect_match():
    assert _score({ELBOW: 170.0, SHOULDER: 90.0}) == 1.0


def test_score_drops_with_error():
    assert 0.0 < _score({ELBOW: 160.0, SHOULDER: 85.0}) < 1.0


def test_higher_error_scores_lower():
    assert _score({ELBOW: 165.0, SHOULDER: 90.0}) > _score({ELBOW: 160.0, SHOULDER: 90.0})


def test_min_aggregation_uses_worst_joint():
    # Shoulder error = 10 = tolerance, despite perfect elbow.
    assert _score({ELBOW: 170.0, SHOULDER: 80.0}) == pytest.approx(0.0)


def test_masked_joint_is_ignored():
    assert _score({ELBOW: None, SHOULDER: 90.0}) == pytest.approx(1.0)


def test_all_masked_returns_zero():
    assert _score({ELBOW: None, SHOULDER: None}) == 0.0


def test_best_match_picks_highest_scoring_template():
    bad = GestureTemplate(
        active_joints=[ELBOW],
        target_angles={ELBOW: 10.0},
        tolerance_deg={ELBOW: 5.0},
        gesture_id="g2",
        name="other",
    )
    result = PoseMatcher().best_match(
        {ELBOW: 170.0, SHOULDER: 90.0}, [bad, _template()], timestamp=1.0
    )
    assert result is not None
    assert result.gesture_id == "g1"
    assert result.timestamp == 1.0


def test_best_match_empty_returns_none():
    assert PoseMatcher().best_match({ELBOW: 90.0, SHOULDER: 90.0}, []) is None
