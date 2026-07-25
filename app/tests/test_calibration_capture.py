import pytest

from app.calibration_capture import CalibrationCaptureController, CapturePhase


def _pose(offset=0.0):
    return {
        "left_elbow": 90.0 + offset,
        "right_elbow": 100.0 + offset,
        "left_shoulder": 45.0 + offset,
        "right_shoulder": 55.0 + offset,
    }


def test_recording_waits_for_three_second_preparation_countdown():
    controller = CalibrationCaptureController()
    controller.start(0.0, 10)

    assert controller.remaining_seconds(0.0) == 3
    assert controller.update(_pose(), 2.99) is False
    assert controller.phase == CapturePhase.COUNTDOWN
    assert controller.frames == []

    controller.update(_pose(), 3.0)
    assert controller.phase == CapturePhase.WAITING
    assert controller.frames == []


def test_small_pose_jitter_does_not_start_recording():
    controller = CalibrationCaptureController()
    controller.start(0.0, 10)
    controller.update(_pose(), 3.0)

    assert controller.update(_pose(3), 3.2) is False
    assert controller.update(_pose(5), 3.4) is False
    assert controller.phase == CapturePhase.WAITING
    assert controller.frames == []


def test_motion_start_keeps_baseline_and_pre_roll():
    controller = CalibrationCaptureController()
    controller.start(0.0, 10)

    controller.update(_pose(), 1.0)
    controller.update(_pose(), 2.0)
    controller.update(_pose(), 3.0)
    controller.update(_pose(20), 3.2)
    controller.update(_pose(40), 3.4)

    assert controller.phase == CapturePhase.RECORDING
    assert controller.frames[0]["left_elbow"] == 90.0
    assert controller.frames[-1]["left_elbow"] == 130.0


def test_stable_final_pose_completes_recording_automatically():
    controller = CalibrationCaptureController()
    controller.start(0.0, 10)

    controller.update(_pose(), 3.0)
    controller.update(_pose(20), 3.2)
    controller.update(_pose(40), 3.4)
    controller.update(_pose(45), 3.5)
    controller.update(_pose(45), 4.0)
    assert controller.update(_pose(45), 4.5) is True
    assert controller.phase == CapturePhase.CAPTURED
    assert controller._largest_range(controller.frames) >= 45.0


def test_configured_duration_is_a_safety_limit_after_motion_starts():
    controller = CalibrationCaptureController()
    controller.start(0.0, 2)

    controller.update(_pose(), 3.0)
    controller.update(_pose(20), 3.2)
    controller.update(_pose(40), 3.4)
    assert controller.remaining_seconds(3.4) == 2
    assert controller.update(_pose(50), 5.39) is False
    assert controller.update(_pose(60), 5.4) is True
    assert controller.phase == CapturePhase.CAPTURED


@pytest.mark.parametrize("duration", [0, 0.5, 61, float("nan")])
def test_invalid_recording_duration_is_rejected(duration):
    controller = CalibrationCaptureController()
    with pytest.raises(ValueError, match="Recording duration"):
        controller.start(0.0, duration)


def test_pose_held_at_orientation_seam_counts_as_stable():

    controller = CalibrationCaptureController()
    controller.start(0.0, 10)

    def frame(orientation):
        return {"l_upper_arm": orientation}

    for t in (0.5, 1.0, 2.0, 2.9):
        controller.update(frame(140.0), t)

    controller.update(frame(140.0), 3.0)
    for step, t in enumerate((3.1, 3.2, 3.3, 3.4)):
        controller.update(frame(150.0 + 10.0 * step), t)
    assert controller.phase == CapturePhase.RECORDING


    captured = False
    for i, t in enumerate((3.5, 3.7, 4.0, 4.2, 4.5)):
        jitter = 179.5 if i % 2 else -179.5
        captured = controller.update(frame(jitter), t)
    assert captured is True
    assert controller.phase == CapturePhase.CAPTURED
