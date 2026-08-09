import tempfile
import unittest
from pathlib import Path

from app.gestures.gesture_matcher import GestureMatcher, GestureMatchEvent
from app.gestures.gesture_store import GestureStore, SavedGesture
from backend.matching_engine.core.angles import AngleKey
from backend.pose_types import BlazePose33, PoseLandmarks


def _save_motion(
    store: GestureStore,
    gesture_id: str,
    values: list[float],
    *,
    joint: str = "L_ELBOW",
    name: str | None = None,
) -> None:
    store.save(
        SavedGesture(
            gesture_id=gesture_id,
            name=name or gesture_id.replace("_", " ").title(),
            active_joints=[joint],
            trajectory=[{joint: value} for value in values],
        )
    )


class GestureMatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gestures_dir = Path(self.temp_dir.name)
        self.store = GestureStore(self.gestures_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_constructor_uses_injected_store(self) -> None:
        matcher = GestureMatcher(self.store)

        self.assertIs(matcher.store, self.store)

    def test_event_serializes_bridge_keys(self) -> None:
        event = GestureMatchEvent(
            gesture_id="wave",
            name="Wave",
            score=0.9,
            timestamp=1.0,
            matched=True,
            has_templates=True,
        )

        payload = event.to_dict()

        self.assertEqual(
            payload,
            {
                "gestureId": "wave",
                "name": "Wave",
                "score": 0.9,
                "timestamp": 1.0,
                "matched": True,
                "hasTemplates": True,
                "threshold": 0.75,
            },
        )

    def test_match_pose_without_templates_reports_empty_state(self) -> None:
        event = GestureMatcher(self.store).match_pose(PoseLandmarks.empty())

        self.assertIsNone(event.gesture_id)
        self.assertFalse(event.matched)
        self.assertFalse(event.has_templates)

    def test_match_pose_without_pose_clears_match(self) -> None:
        _save_motion(self.store, "elbow_sweep", [60.0, 90.0, 120.0])
        matcher = GestureMatcher(self.store)

        event = matcher.match_pose(None)

        self.assertIsNone(event.gesture_id)
        self.assertFalse(event.matched)
        self.assertTrue(event.has_templates)

    def test_angles_for_pose_returns_empty_dict_for_missing_pose(self) -> None:
        self.assertEqual(GestureMatcher(self.store).angles_for_pose(None), {})

    def test_angles_for_pose_uses_image_plane_instead_of_noisy_depth(self) -> None:
        matcher = GestureMatcher(self.store)
        pose = PoseLandmarks.empty()
        pose.visibility[:] = 1.0
        pose.xyz[BlazePose33.L_SHOULDER] = [0.0, 0.0, 5.0]
        pose.xyz[BlazePose33.L_ELBOW] = [1.0, 0.0, -5.0]
        pose.xyz[BlazePose33.L_WRIST] = [1.0, 1.0, 8.0]

        angles = matcher.angles_for_pose(pose)

        self.assertAlmostEqual(angles[AngleKey.L_ELBOW], 90.0)

    def test_set_active_gestures_filters_unbound_templates(self) -> None:
        _save_motion(self.store, "elbow_sweep", [60.0, 90.0, 120.0])
        matcher = GestureMatcher(self.store)

        matcher.set_active_gestures([], {})
        event = matcher.match_pose(PoseLandmarks.empty())

        self.assertFalse(event.has_templates)

    def test_reload_preserves_active_filter_and_threshold(self) -> None:
        matcher = GestureMatcher(self.store)
        matcher.set_active_gestures(["elbow_sweep"], {"elbow_sweep": 0.9})
        _save_motion(self.store, "elbow_sweep", [60.0, 90.0, 120.0])

        matcher.reload_templates()

        self.assertEqual(
            [template.gesture_id for template in matcher._active_templates],
            ["elbow_sweep"],
        )
        self.assertEqual(matcher.match_thresholds["elbow_sweep"], 0.9)
        self.assertEqual(matcher.active_angle_keys, {AngleKey.L_ELBOW})

    def test_bound_angle_keys_are_union_of_bound_motion_joints(self) -> None:
        _save_motion(self.store, "left_arm", [60.0, 90.0, 120.0])
        _save_motion(
            self.store,
            "right_leg",
            [50.0, 80.0, 110.0],
            joint="R_KNEE",
        )
        matcher = GestureMatcher(self.store)

        matcher.set_active_gestures(["left_arm", "right_leg"])

        self.assertEqual(
            matcher.bound_angle_keys,
            {AngleKey.L_ELBOW, AngleKey.R_KNEE},
        )

    def test_motion_template_matches_and_reports_threshold(self) -> None:
        frames = [80.0, 120.0, 160.0]
        _save_motion(
            self.store,
            "elbow_sweep",
            frames,
            name="Elbow Sweep",
        )
        matcher = GestureMatcher(self.store)

        event = None
        for value in frames:
            event = matcher.match_pose(
                PoseLandmarks.empty(),
                angles={AngleKey.L_ELBOW: value},
            )

        self.assertIsNotNone(event)
        self.assertEqual(event.gesture_id, "elbow_sweep")
        self.assertTrue(event.matched)
        self.assertEqual(event.threshold, 0.75)

    def test_completed_motion_matches_only_once(self) -> None:
        trajectory = [60.0 + index * 2.0 for index in range(32)]
        _save_motion(self.store, "elbow_sweep", trajectory)
        matcher = GestureMatcher(self.store, match_threshold=0.75)

        events = [
            matcher.match_pose(
                PoseLandmarks.empty(),
                angles={AngleKey.L_ELBOW: value},
            )
            for value in trajectory
        ]

        matched_events = [event for event in events if event.matched]
        self.assertEqual(len(matched_events), 1)
        self.assertEqual(matched_events[0].gesture_id, "elbow_sweep")

    def test_nearly_static_motion_template_cannot_match_held_pose(self) -> None:
        _save_motion(
            self.store,
            "static_elbow",
            [45.0, 47.0, 44.0, 46.0, 45.0],
        )
        matcher = GestureMatcher(self.store, match_threshold=0.75)

        event = None
        for _ in range(40):
            event = matcher.match_pose(
                PoseLandmarks.empty(),
                angles={AngleKey.L_ELBOW: 45.0},
            )

        self.assertIsNotNone(event)
        self.assertEqual(event.gesture_id, "static_elbow")
        self.assertEqual(event.score, 0.0)
        self.assertFalse(event.matched)


if __name__ == "__main__":
    unittest.main()
