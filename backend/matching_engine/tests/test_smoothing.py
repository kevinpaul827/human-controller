"""Tests for the AngleSmoother (per-joint EMA)."""

import pytest

from backend.matching_engine.core.angles import AngleKey
from backend.matching_engine.smoothing import AngleSmoother

E = AngleKey.L_ELBOW


def test_first_frame_passes_through():
    s = AngleSmoother(alpha=0.25)
    assert s.update({E: 100.0})[E] == 100.0


def test_ema_moves_toward_new_value():
    s = AngleSmoother(alpha=0.5, deadband_deg=0.0)
    s.update({E: 100.0})
    # 100 + 0.5*(120-100) = 110
    assert s.update({E: 120.0})[E] == pytest.approx(110.0)


def test_deadband_holds_small_changes():
    s = AngleSmoother(alpha=0.5, deadband_deg=2.0)
    s.update({E: 100.0})
    assert s.update({E: 101.0})[E] == 100.0
    assert s.update({E: 99.5})[E] == 100.0
    assert s.update({E: 110.0})[E] == pytest.approx(105.0)


def test_smoother_dampens_jitter():
    s = AngleSmoother(alpha=0.25)
    out = [s.update({E: v})[E] for v in (90.0, 110.0, 90.0, 110.0, 90.0, 110.0)]
    import statistics

    assert statistics.pstdev(out) < 8.0


def test_masked_joint_passes_through_and_resets():
    s = AngleSmoother(alpha=0.5)
    s.update({E: 100.0})
    assert s.update({E: None})[E] is None
    assert s.update({E: 50.0})[E] == 50.0


def test_alpha_one_is_passthrough():
    s = AngleSmoother(alpha=1.0)
    s.update({E: 100.0})
    assert s.update({E: 130.0})[E] == 130.0


def test_invalid_alpha():
    with pytest.raises(ValueError):
        AngleSmoother(alpha=0.0)
