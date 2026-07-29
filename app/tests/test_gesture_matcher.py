import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.gesture_matcher import GestureMatcher
from app.gesture_store import SavedGesture
from backend.matching_engine.core.angles import AngleKey
from backend.pose_types import BlazePose33, PoseLandmarks


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
        self.assertEqual(event.gestureType, "state")
        self.assertEqual(event.threshold, 0.75)
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

    def test_angles_for_pose_uses_image_plane_instead_of_noisy_depth(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)
        pose = PoseLandmarks.empty()
        pose.visibility[:] = 1.0
        pose.xyz[BlazePose33.L_SHOULDER] = [0.0, 0.0, 5.0]
        pose.xyz[BlazePose33.L_ELBOW] = [1.0, 0.0, -5.0]
        pose.xyz[BlazePose33.L_WRIST] = [1.0, 1.0, 8.0]

        angles = matcher.angles_for_pose(pose)

        self.assertAlmostEqual(angles[AngleKey.L_ELBOW], 90.0)

    def test_set_active_gestures_filters_unbound_templates(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)
        matcher.store.create_or_update(
            gesture_id="raise_left_arm",
            name="Raise Left Arm",
            regions=["left_arm"],
            active_joints=["L_ELBOW"],
            target_angles={"L_ELBOW": 170.0},
        )
        matcher.reload_templates()

        matcher.set_active_gestures([], {})
        event = matcher.match_pose(PoseLandmarks.empty())

        self.assertFalse(event.hasTemplates)
        self.assertFalse(event.matched)

    def test_reload_preserves_active_gesture_filter_and_threshold(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)
        matcher.set_active_gestures(["raise_left_arm"], {"raise_left_arm": 0.9})
        matcher.store.create_or_update(
            gesture_id="raise_left_arm",
            name="Raise Left Arm",
            regions=["left_arm"],
            active_joints=["L_ELBOW"],
            target_angles={"L_ELBOW": 170.0},
        )

        matcher.reload_templates()

        self.assertEqual(
            [template.gesture_id for template in matcher._templates],
            ["raise_left_arm"],
        )
        self.assertEqual(matcher._match_thresholds["raise_left_arm"], 0.9)
        self.assertEqual(matcher.active_angle_keys, {AngleKey.L_ELBOW})

    def test_bound_angle_keys_are_union_of_all_bound_gesture_joints(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)
        matcher.store.create_or_update(
            gesture_id="left_arm",
            name="Left Arm",
            regions=["left_arm"],
            active_joints=["L_ELBOW", "L_SHOULDER_ABD"],
            target_angles={"L_ELBOW": 170.0, "L_SHOULDER_ABD": 80.0},
        )
        matcher.store.create_or_update(
            gesture_id="right_leg",
            name="Right Leg",
            regions=["right_leg"],
            active_joints=["R_KNEE"],
            target_angles={"R_KNEE": 120.0},
        )
        matcher.reload_templates()

        matcher.set_active_gestures(["left_arm", "right_leg"])

        self.assertEqual(
            matcher.bound_angle_keys,
            {AngleKey.L_ELBOW, AngleKey.L_SHOULDER_ABD, AngleKey.R_KNEE},
        )

    def test_match_pose_uses_precomputed_angles_and_binding_threshold(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)
        matcher.store.create_or_update(
            gesture_id="raise_left_arm",
            name="Raise Left Arm",
            regions=["left_arm"],
            active_joints=["L_ELBOW"],
            target_angles={"L_ELBOW": 170.0},
            tolerance_deg={"L_ELBOW": 20.0},
        )
        matcher.reload_templates()
        matcher.set_active_gestures(["raise_left_arm"], {"raise_left_arm": 0.8})

        with patch.object(
            matcher.feature_extractor,
            "to_angles",
            side_effect=AssertionError("angles should not be recalculated"),
        ):
            event = matcher.match_pose(
                PoseLandmarks.empty(),
                angles={AngleKey.L_ELBOW: 165.0},
            )

        self.assertEqual(event.gestureId, "raise_left_arm")
        self.assertEqual(event.score, 0.75)
        self.assertEqual(event.threshold, 0.8)
        self.assertFalse(event.matched)

    def test_passing_gesture_wins_over_higher_non_passing_score(self) -> None:
        matcher = GestureMatcher(self.gestures_dir, match_threshold=0.75)
        matcher.store.create_or_update(
            gesture_id="strict",
            name="Strict",
            regions=["left_arm"],
            active_joints=["L_ELBOW"],
            target_angles={"L_ELBOW": 0.0},
            tolerance_deg={"L_ELBOW": 100.0},
        )
        matcher.store.create_or_update(
            gesture_id="permissive",
            name="Permissive",
            regions=["right_leg"],
            active_joints=["R_KNEE"],
            target_angles={"R_KNEE": 0.0},
            tolerance_deg={"R_KNEE": 100.0},
        )
        matcher.reload_templates()
        matcher.set_active_gestures(
            ["strict", "permissive"],
            {"strict": 0.9, "permissive": 0.65},
        )

        event = matcher.match_pose(
            PoseLandmarks.empty(),
            angles={AngleKey.L_ELBOW: 20.0, AngleKey.R_KNEE: 30.0},
        )

        self.assertEqual(event.gestureId, "permissive")
        self.assertTrue(event.matched)
        self.assertAlmostEqual(event.score, 0.7)

    def test_motion_template_uses_motion_matcher_and_reports_type(self) -> None:
        matcher = GestureMatcher(self.gestures_dir)
        frames = [
            {"L_ELBOW": 80.0},
            {"L_ELBOW": 120.0},
            {"L_ELBOW": 160.0},
        ]
        matcher.store.save(
            SavedGesture(
                gesture_id="elbow_sweep",
                name="Elbow Sweep",
                type="motion",
                active_joints=["L_ELBOW"],
                trajectory=frames,
            )
        )
        matcher.reload_templates()

        event = None
        for frame in frames:
            event = matcher.match_pose(
                PoseLandmarks.empty(),
                angles={AngleKey.L_ELBOW: frame["L_ELBOW"]},
            )

        self.assertIsNotNone(event)
        self.assertEqual(event.gestureId, "elbow_sweep")
        self.assertEqual(event.gestureType, "motion")
        self.assertTrue(event.matched)

    def test_completed_motion_matches_only_once(self) -> None:
        matcher = GestureMatcher(self.gestures_dir, match_threshold=0.75)
        trajectory = [
            {"L_ELBOW": 60.0 + index * 2.0}
            for index in range(32)
        ]
        matcher.store.save(
            SavedGesture(
                gesture_id="elbow_sweep",
                name="Elbow Sweep",
                type="motion",
                active_joints=["L_ELBOW"],
                trajectory=trajectory,
            )
        )
        matcher.reload_templates()

        events = [
            matcher.match_pose(
                PoseLandmarks.empty(),
                angles={AngleKey.L_ELBOW: frame["L_ELBOW"]},
            )
            for frame in trajectory
        ]

        matched_events = [event for event in events if event.matched]
        self.assertEqual(len(matched_events), 1)
        self.assertEqual(matched_events[0].gestureId, "elbow_sweep")

    def test_nearly_static_motion_template_cannot_match_held_pose(self) -> None:
        matcher = GestureMatcher(self.gestures_dir, match_threshold=0.75)
        matcher.store.save(
            SavedGesture(
                gesture_id="static_elbow",
                name="Static Elbow",
                type="motion",
                active_joints=["L_ELBOW"],
                trajectory=[
                    {"L_ELBOW": value}
                    for value in (45.0, 47.0, 44.0, 46.0, 45.0)
                ],
            )
        )
        matcher.reload_templates()

        event = None
        for _ in range(40):
            event = matcher.match_pose(
                PoseLandmarks.empty(),
                angles={AngleKey.L_ELBOW: 45.0},
            )

        self.assertIsNotNone(event)
        self.assertEqual(event.gestureId, "static_elbow")
        self.assertEqual(event.score, 0.0)
        self.assertFalse(event.matched)


if __name__ == "__main__":
    unittest.main()
