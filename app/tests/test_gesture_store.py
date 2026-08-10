import tempfile
import unittest
from pathlib import Path

from app.gestures.gesture_store import GestureStore, SavedGesture
from backend.matching_engine.core.angles import AngleKey
from backend.matching_engine.core.types import GestureTemplate


class GestureStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gestures_dir = Path(self.temp_dir.name)
        self.store = GestureStore(self.gestures_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_motion_saves_one_json_per_gesture(self) -> None:
        gesture = self.store.create_motion(
            name="Elbow Bend",
            active_joints=["R_ELBOW"],
            trajectory=[{"R_ELBOW": 42.0}, {"R_ELBOW": 90.0}],
        )

        saved_path = self.gestures_dir / f"{gesture.gesture_id}.json"
        self.assertTrue(saved_path.exists())

        loaded = self.store.load(gesture.gesture_id)
        self.assertEqual(loaded.name, "Elbow Bend")
        self.assertEqual(loaded.active_joints, ["R_ELBOW"])
        self.assertEqual(loaded.trajectory[0]["R_ELBOW"], 42.0)

    def test_load_all_returns_gestures_sorted_by_name(self) -> None:
        self.store.create_motion(
            gesture_id="squat",
            name="Squat",
            active_joints=["L_KNEE", "R_KNEE"],
            trajectory=[
                {"L_KNEE": 60.0, "R_KNEE": 60.0},
                {"L_KNEE": 90.0, "R_KNEE": 90.0},
            ],
        )
        self.store.create_motion(
            gesture_id="arm_raise",
            name="Arm Raise",
            active_joints=["R_SHOULDER_ABD"],
            trajectory=[
                {"R_SHOULDER_ABD": 60.0},
                {"R_SHOULDER_ABD": 120.0},
            ],
        )

        gestures = self.store.load_all()
        self.assertEqual([gesture.name for gesture in gestures], ["Arm Raise", "Squat"])

    def test_template_mapping_round_trips_motion_data(self) -> None:
        template = GestureTemplate(
            name="Wave",
            gesture_id="wave",
            active_joints=[AngleKey.L_ELBOW],
            trajectory=[{AngleKey.L_ELBOW: 45.0}],
        )

        saved = SavedGesture.from_template(template)
        restored = saved.to_template()

        self.assertEqual(saved.trajectory, [{"L_ELBOW": 45.0}])
        self.assertEqual(restored, template)

    def test_delete_removes_json_and_allows_same_id_to_be_re_recorded(self) -> None:
        gesture = self.store.create_motion(
            gesture_id="arm_raise",
            name="Arm Raise",
            active_joints=["R_SHOULDER_ABD"],
            trajectory=[
                {"R_SHOULDER_ABD": 60.0},
                {"R_SHOULDER_ABD": 120.0},
            ],
        )

        self.store.delete(gesture.gesture_id)

        self.assertFalse(self.store.gesture_path(gesture.gesture_id).exists())
        replacement = self.store.create_motion(
            gesture_id=gesture.gesture_id,
            name="Arm Raise Re-recorded",
            active_joints=["R_SHOULDER_ABD"],
            trajectory=[
                {"R_SHOULDER_ABD": 60.0},
                {"R_SHOULDER_ABD": 130.0},
            ],
        )
        self.assertEqual(self.store.load(replacement.gesture_id).name, replacement.name)

    def test_delete_missing_gesture_is_idempotent(self) -> None:
        self.store.delete("missing")

        self.assertEqual(self.store.load_all(), [])

    def test_gesture_id_cannot_escape_the_gesture_directory(self) -> None:
        outside = self.gestures_dir.parent / "outside.json"
        outside.write_text("keep", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "must not contain a path"):
            self.store.delete("../outside")

        self.assertEqual(outside.read_text(encoding="utf-8"), "keep")

    def test_state_gesture_files_are_ignored(self) -> None:
        (self.gestures_dir / "legacy.json").write_text(
            '{"gesture_id":"legacy","name":"Legacy","type":"state"}',
            encoding="utf-8",
        )

        self.assertEqual(self.store.load_all(), [])

    def test_malformed_motion_gesture_files_are_ignored(self) -> None:
        (self.gestures_dir / "invalid.json").write_text(
            '{"gesture_id":"invalid","name":"Invalid","type":"motion",'
            '"active_joints":["UNKNOWN"],"trajectory":[{"UNKNOWN":90}]}',
            encoding="utf-8",
        )

        self.assertEqual(self.store.load_all(), [])

    def test_save_rejects_invalid_motion_data(self) -> None:
        with self.assertRaises(ValueError):
            self.store.save(
                SavedGesture(
                    gesture_id="invalid",
                    name="Invalid",
                    active_joints=["UNKNOWN"],
                    trajectory=[{"UNKNOWN": 90.0}],
                )
            )


if __name__ == "__main__":
    unittest.main()
