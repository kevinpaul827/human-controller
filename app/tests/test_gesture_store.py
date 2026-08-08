import tempfile
import unittest
from pathlib import Path

from app.gestures.gesture_store import GestureStore, CURRENT_ACTION_SCHEMA_VERSION


class GestureStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gestures_dir = Path(self.temp_dir.name)
        self.store = GestureStore(self.gestures_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_or_update_saves_one_json_per_gesture(self) -> None:
        gesture = self.store.create_or_update(
            name="Elbow Bend",
            regions=["right_arm"],
            active_joints=["R_ELBOW"],
            target_angles={"R_ELBOW": 42.0},
            tolerance_deg={"R_ELBOW": 15.0},
        )

        saved_path = self.gestures_dir / f"{gesture.gesture_id}.json"
        self.assertTrue(saved_path.exists())

        loaded = self.store.load(gesture.gesture_id)
        self.assertEqual(loaded.schemaVersion, CURRENT_ACTION_SCHEMA_VERSION)
        self.assertEqual(loaded.name, "Elbow Bend")
        self.assertEqual(loaded.regions, ["right_arm"])
        self.assertEqual(loaded.active_joints, ["R_ELBOW"])
        self.assertEqual(loaded.target_angles["R_ELBOW"], 42.0)

    def test_load_all_returns_gestures_sorted_by_name(self) -> None:
        self.store.create_or_update(
            gesture_id="squat",
            name="Squat",
            regions=["legs"],
            active_joints=["L_KNEE", "R_KNEE"],
            target_angles={"L_KNEE": 90.0, "R_KNEE": 90.0},
        )
        self.store.create_or_update(
            gesture_id="arm_raise",
            name="Arm Raise",
            regions=["right_arm"],
            active_joints=["R_SHOULDER_ABD"],
            target_angles={"R_SHOULDER_ABD": 120.0},
        )

        gestures = self.store.load_all()
        self.assertEqual([gesture.name for gesture in gestures], ["Arm Raise", "Squat"])

    def test_delete_removes_json_and_allows_same_id_to_be_re_recorded(self) -> None:
        gesture = self.store.create_or_update(
            gesture_id="arm_raise",
            name="Arm Raise",
            regions=["right_arm"],
            active_joints=["R_SHOULDER_ABD"],
            target_angles={"R_SHOULDER_ABD": 120.0},
        )

        self.store.delete(gesture.gesture_id)

        self.assertFalse(self.store.gesture_path(gesture.gesture_id).exists())
        replacement = self.store.create_or_update(
            gesture_id=gesture.gesture_id,
            name="Arm Raise Re-recorded",
            regions=["right_arm"],
            active_joints=["R_SHOULDER_ABD"],
            target_angles={"R_SHOULDER_ABD": 130.0},
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


if __name__ == "__main__":
    unittest.main()
