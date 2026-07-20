import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.gesture_matcher import GestureMatcher
from backend.matching_engine.core.angles import AngleKey
from backend.pose_types import PoseLandmarks


class GestureMatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gestures_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_match_pose_returns_best_match_payload(self) -> None:
        matcher = GestureMatcher(self.gestures_dir, match_threshold=0.75)
        matcher.store.create_or_update(
            gesture_id="raise_left_arm",
            name="Raise Left Arm",
            regions=["left_arm"],
            active_joints=["L_ELBOW", "L_SHOULDER_ABD"],
            target_angles={"L_ELBOW": 170.0, "L_SHOULDER_ABD": 90.0},
            tolerance_deg={"L_ELBOW": 20.0, "L_SHOULDER_ABD": 10.0},
        )
        matcher.reload_templates()

        pose = PoseLandmarks.empty()
        with patch.object(
            matcher.feature_extractor,
            "to_angles",
            return_value={
                AngleKey.L_ELBOW: 170.0,
                AngleKey.L_SHOULDER_ABD: 90.0,
            },
        ):
            event = matcher.match_pose(pose)

        self.assertEqual(event.gestureId, "raise_left_arm")
        self.assertEqual(event.name, "Raise Left Arm")
        self.assertTrue(event.matched)
        self.assertTrue(event.hasTemplates)
        self.assertGreaterEqual(event.score, 0.99)
        self.assertIsNotNone(event.timestamp)

    def test_match_pose_without_templates_reports_empty_state(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)

        event = matcher.match_pose(PoseLandmarks.empty())

        self.assertIsNone(event.gestureId)
        self.assertIsNone(event.name)
        self.assertFalse(event.matched)
        self.assertFalse(event.hasTemplates)
        self.assertEqual(event.score, 0.0)
        self.assertIsNone(event.timestamp)

    def test_match_pose_without_pose_clears_match(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)
        matcher.store.create_or_update(
            gesture_id="raise_left_arm",
            name="Raise Left Arm",
            regions=["left_arm"],
            active_joints=["L_ELBOW"],
            target_angles={"L_ELBOW": 170.0},
        )
        matcher.reload_templates()

        event = matcher.match_pose(None)

        self.assertIsNone(event.gestureId)
        self.assertIsNone(event.name)
        self.assertFalse(event.matched)
        self.assertTrue(event.hasTemplates)
        self.assertEqual(event.score, 0.0)
        self.assertIsNone(event.timestamp)

    def test_angles_for_pose_returns_empty_dict_for_missing_pose(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)

        self.assertEqual(matcher.angles_for_pose(None), {})


if __name__ == "__main__":
    unittest.main()
