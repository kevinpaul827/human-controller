import tempfile
import unittest
from pathlib import Path

from backend.matching_engine import AngleKey

from app.calibration.calibration_service import CalibrationService
from app.gestures.gesture_store import GestureStore


class CalibrationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 0.0
        self.updates = []
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store = GestureStore(Path(self.temp_dir.name))
        self.service = CalibrationService(
            self.store,
            clock=lambda: self.now,
            on_update=self.updates.append,
        )

    def test_manual_capture_builds_and_persists_a_static_template(self) -> None:
        self.service.add_pose_angles({AngleKey.L_ELBOW: 80.0})
        self.service.add_pose_angles({AngleKey.L_ELBOW: 100.0})

        captured = self.service.capture_rep()
        saved = self.service.save_rep("Held elbow", "held_elbow")
        gesture = self.store.load("held_elbow")

        self.assertEqual(captured["angles"], {"L_ELBOW": 90.0})
        self.assertEqual(saved["gestureId"], "held_elbow")
        self.assertEqual(gesture.type, "state")
        self.assertEqual(gesture.trajectory, [])
        self.assertEqual(self.updates[-1]["repCount"], 0)

    def test_recorded_motion_is_persisted_as_a_motion_template(self) -> None:
        self.service.start_rep(10)
        for timestamp, angle in ((1.0, 90.0), (3.0, 90.0), (3.2, 110.0), (3.4, 130.0)):
            self.now = timestamp
            self.service.add_pose_angles({AngleKey.L_ELBOW: angle})

        captured = self.service.stop_rep()
        self.service.save_rep("Elbow sweep", "elbow_sweep")
        gesture = self.store.load("elbow_sweep")

        self.assertEqual(captured["repCount"], 1)
        self.assertEqual(gesture.type, "motion")
        self.assertEqual(len(gesture.trajectory), 32)

    def test_cancel_discards_only_the_in_progress_recording(self) -> None:
        self.service.start_rep()
        self.service.cancel()

        self.assertFalse(self.service.recording)
        self.assertEqual(self.service.capture_phase.value, "idle")


if __name__ == "__main__":
    unittest.main()
