import math
import unittest

from app.calibration.calibration_capture import CalibrationCaptureController, CapturePhase


def _pose(offset=0.0):
    return {
        "left_elbow": 90.0 + offset,
        "right_elbow": 100.0 + offset,
        "left_shoulder": 45.0 + offset,
        "right_shoulder": 55.0 + offset,
    }


class CalibrationCaptureTests(unittest.TestCase):
    def test_recording_waits_for_three_second_preparation_countdown(self):
        controller = CalibrationCaptureController()
        controller.start(0.0, 10)

        self.assertEqual(controller.remaining_seconds(0.0), 3)
        self.assertFalse(controller.update(_pose(), 2.99))
        self.assertEqual(controller.phase, CapturePhase.COUNTDOWN)
        self.assertEqual(controller.frames, [])

        controller.update(_pose(), 3.0)
        self.assertEqual(controller.phase, CapturePhase.WAITING)
        self.assertEqual(controller.frames, [])

    def test_small_pose_jitter_does_not_start_recording(self):
        controller = CalibrationCaptureController()
        controller.start(0.0, 10)
        controller.update(_pose(), 3.0)

        self.assertFalse(controller.update(_pose(3), 3.2))
        self.assertFalse(controller.update(_pose(5), 3.4))
        self.assertEqual(controller.phase, CapturePhase.WAITING)
        self.assertEqual(controller.frames, [])

    def test_motion_start_keeps_baseline_and_pre_roll(self):
        controller = CalibrationCaptureController()
        controller.start(0.0, 10)

        controller.update(_pose(), 1.0)
        controller.update(_pose(), 2.0)
        controller.update(_pose(), 3.0)
        controller.update(_pose(20), 3.2)
        controller.update(_pose(40), 3.4)

        self.assertEqual(controller.phase, CapturePhase.RECORDING)
        self.assertEqual(controller.frames[0]["left_elbow"], 90.0)
        self.assertEqual(controller.frames[-1]["left_elbow"], 130.0)

    def test_stable_final_pose_completes_recording_automatically(self):
        controller = CalibrationCaptureController()
        controller.start(0.0, 10)

        controller.update(_pose(), 3.0)
        controller.update(_pose(20), 3.2)
        controller.update(_pose(40), 3.4)
        controller.update(_pose(45), 3.5)
        controller.update(_pose(45), 4.0)
        self.assertTrue(controller.update(_pose(45), 4.5))
        self.assertEqual(controller.phase, CapturePhase.CAPTURED)
        self.assertGreaterEqual(controller._largest_range(controller.frames), 45.0)

    def test_configured_duration_is_a_safety_limit_after_motion_starts(self):
        controller = CalibrationCaptureController()
        controller.start(0.0, 2)

        controller.update(_pose(), 3.0)
        controller.update(_pose(20), 3.2)
        controller.update(_pose(40), 3.4)
        self.assertEqual(controller.remaining_seconds(3.4), 2)
        self.assertFalse(controller.update(_pose(50), 5.39))
        self.assertTrue(controller.update(_pose(60), 5.4))
        self.assertEqual(controller.phase, CapturePhase.CAPTURED)

    def test_invalid_recording_duration_is_rejected(self):
        for duration in (0, 0.5, 61, math.nan):
            with self.subTest(duration=duration):
                controller = CalibrationCaptureController()
                with self.assertRaisesRegex(ValueError, "Recording duration"):
                    controller.start(0.0, duration)

    def test_pose_held_at_orientation_seam_counts_as_stable(self):
        controller = CalibrationCaptureController()
        controller.start(0.0, 10)

        def frame(orientation):
            return {"l_upper_arm": orientation}

        for timestamp in (0.5, 1.0, 2.0, 2.9):
            controller.update(frame(140.0), timestamp)

        controller.update(frame(140.0), 3.0)
        for step, timestamp in enumerate((3.1, 3.2, 3.3, 3.4)):
            controller.update(frame(150.0 + 10.0 * step), timestamp)
        self.assertEqual(controller.phase, CapturePhase.RECORDING)

        captured = False
        for index, timestamp in enumerate((3.5, 3.7, 4.0, 4.2, 4.5)):
            jitter = 179.5 if index % 2 else -179.5
            captured = controller.update(frame(jitter), timestamp)
        self.assertTrue(captured)
        self.assertEqual(controller.phase, CapturePhase.CAPTURED)


if __name__ == "__main__":
    unittest.main()
