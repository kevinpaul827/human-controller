import tempfile
import unittest
import json
import math
from pathlib import Path
from unittest.mock import patch

from app.bridges.state_bridge import StateBridge
from app.gestures.gesture_store import GestureStore
from app.profile_manager import ProfileManager


class StateBridgeThresholdTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.bridge = StateBridge(
            self.data_dir,
            GestureStore(self.data_dir / "gestures"),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_binding_thresholds_round_trip_into_runtime_configuration(self):
        current = self.bridge.getState()
        patient_id = current["patients"][0]["patientId"]
        current["selectedPatientId"] = patient_id
        current["bindings"] = [
            {"gestureId": "elbow", "key": "W", "matchThreshold": 63}
        ]

        saved = self.bridge.saveState(current)
        runtime = self.bridge.runtime_configuration()

        self.assertEqual(saved["bindings"][0]["matchThreshold"], 63)
        self.assertEqual(runtime["bindings"], {"elbow": "W"})
        self.assertEqual(runtime["matchThresholds"], {"elbow": 63})

    def test_pose_model_defaults_to_lite(self):
        self.assertEqual(self.bridge.getState()["settings"]["poseModel"], "lite")
        self.assertEqual(
            self.bridge.runtime_configuration()["settings"]["poseModel"],
            "lite",
        )

    def test_pose_model_round_trips_into_runtime_configuration(self):
        current = self.bridge.getState()
        current["settings"]["poseModel"] = "heavy"
        runtime_updates = []
        self.bridge.runtimeConfigurationChanged.connect(runtime_updates.append)

        saved = self.bridge.saveState(current)

        self.assertEqual(saved["settings"]["poseModel"], "heavy")
        self.assertEqual(
            self.bridge.runtime_configuration()["settings"]["poseModel"],
            "heavy",
        )
        self.assertEqual(runtime_updates[-1]["settings"]["poseModel"], "heavy")

    def test_invalid_pose_model_falls_back_to_lite(self):
        current = self.bridge.getState()
        current["settings"]["poseModel"] = "unsupported"

        saved = self.bridge.saveState(current)

        self.assertEqual(saved["settings"]["poseModel"], "lite")

    def test_corrupt_state_shapes_fall_back_to_safe_values(self):
        self.bridge.state_path.write_text(
            json.dumps(
                {
                    "presets": None,
                    "pendingGestures": "invalid",
                    "selectedPatientId": ["patient-a"],
                    "settings": "invalid",
                }
            ),
            encoding="utf-8",
        )

        state = self.bridge.getState()

        self.assertEqual(state["presets"], [])
        self.assertIsNone(state["selectedPatientId"])
        self.assertEqual(state["settings"]["matchThreshold"], 75.0)
        self.assertEqual(state["settings"]["poseModel"], "lite")

    def test_invalid_runtime_numbers_are_clamped_or_defaulted(self):
        current = self.bridge.getState()
        current["settings"].update(
            {
                "matchThreshold": "invalid",
                "cooldown": -4,
                "smoothing": 99,
            }
        )

        saved = self.bridge.saveState(current)

        self.assertEqual(saved["settings"]["matchThreshold"], 75.0)
        self.assertEqual(saved["settings"]["cooldown"], 0.0)
        self.assertEqual(saved["settings"]["smoothing"], 4)
        self.assertEqual(
            self.bridge.runtime_configuration()["settings"]["poseModel"],
            "lite",
        )

    @patch("app.bridges.state_bridge.device_pose_recommendation")
    def test_pose_model_recommendation_is_read_only(self, recommend):
        recommend.return_value = {
            "poseModel": "full",
            "ramGb": 8.0,
            "physicalCpuCount": 4,
            "logicalCpuCount": 8,
        }
        runtime_updates = []
        state_updates = []
        self.bridge.runtimeConfigurationChanged.connect(runtime_updates.append)
        self.bridge.stateChanged.connect(state_updates.append)

        result = self.bridge.recommendPoseModel()

        self.assertEqual(result["poseModel"], "full")
        self.assertEqual(runtime_updates, [])
        self.assertEqual(state_updates, [])

    def test_legacy_binding_uses_global_threshold_as_its_default(self):
        current = self.bridge.getState()
        patient_id = current["patients"][0]["patientId"]
        current["selectedPatientId"] = patient_id
        current["settings"]["matchThreshold"] = 71
        current["bindings"] = [{"gestureId": "elbow", "key": "W"}]

        saved = self.bridge.saveState(current)

        self.assertEqual(saved["bindings"][0]["matchThreshold"], 71)

    def test_create_profile_selects_the_new_profile(self):
        created = self.bridge.createProfile("New Patient", "Needs seated controls")
        profile = next(
            item
            for item in created["patients"]
            if item["patientName"] == "New Patient"
        )

        self.assertEqual(created["selectedPatientId"], profile["patientId"])
        self.assertEqual(profile["notes"], "Needs seated controls")

    def test_shared_profile_manager_is_used_by_state_bridge(self):
        manager = ProfileManager(self.data_dir / "shared-profiles")
        bridge = StateBridge(
            self.data_dir / "shared-state",
            GestureStore(self.data_dir / "shared-gestures"),
            manager,
        )

        self.assertIs(bridge.profile_manager, manager)

    def test_fresh_state_starts_unassigned(self):
        snapshot = self.bridge.getState()

        self.assertIsNone(snapshot["selectedPatientId"])
        self.assertTrue(snapshot["patients"])

    def test_delete_selected_profile_clears_selection(self):
        current = self.bridge.getState()
        selected_id = current["patients"][0]["patientId"]
        self.bridge.selectPatient(selected_id)

        updated = self.bridge.deleteProfile(selected_id)

        self.assertIsNone(updated["selectedPatientId"])
        self.assertTrue(updated["patients"])

    def test_delete_all_profiles_produces_empty_runtime(self):
        for profile in list(self.bridge.getState()["patients"]):
            self.bridge.deleteProfile(profile["patientId"])

        snapshot = self.bridge.getState()

        self.assertEqual(snapshot["patients"], [])
        self.assertIsNone(snapshot["selectedPatientId"])
        self.assertEqual(self.bridge.runtime_configuration()["bindings"], {})

    def test_delete_gesture_cleans_profiles_presets_pending_state_and_file(self):
        gesture_store = self.bridge.gesture_store
        gesture_store.create_motion(
            gesture_id="delete_me",
            name="Delete Me",
            regions=["right_arm"],
            active_joints=["R_ELBOW"],
            trajectory=[{"R_ELBOW": 45.0}, {"R_ELBOW": 90.0}],
        )
        current = self.bridge.getState()
        current["bindings"] = [
            {"gestureId": "delete_me", "key": "D", "matchThreshold": 64}
        ]
        current["presets"] = [
            {
                "presetId": "preset-a",
                "name": "Preset A",
                "bindings": [
                    {"gestureId": "delete_me", "key": "D", "matchThreshold": 64}
                ],
            }
        ]
        self.bridge.saveState(current)
        other = next(
            profile
            for profile in self.bridge.profile_manager.list_profiles()
            if profile.patient_id != current["selectedPatientId"]
        )
        other.key_bindings["delete_me"] = "E"
        other.match_thresholds["delete_me"] = 72
        self.bridge.profile_manager.save(other)
        runtime_updates = []
        state_updates = []
        self.bridge.runtimeConfigurationChanged.connect(runtime_updates.append)
        self.bridge.stateChanged.connect(state_updates.append)

        snapshot = self.bridge.deleteGesture("delete_me")

        self.assertFalse(gesture_store.gesture_path("delete_me").exists())
        self.assertEqual(snapshot["bindings"], [])
        self.assertEqual(snapshot["presets"][0]["bindings"], [])
        for profile in self.bridge.profile_manager.list_profiles():
            self.assertNotIn("delete_me", profile.key_bindings)
            self.assertNotIn("delete_me", profile.match_thresholds)
        self.assertEqual(runtime_updates[-1]["bindings"], {})
        self.assertEqual(state_updates[-1], snapshot)

    def test_delete_pending_gesture_removes_it_from_state(self):
        current = self.bridge.getState()
        current["gestures"].append(
            {
                "gestureId": "pending",
                "name": "Pending",
                "matchScore": None,
                "calibratedAt": None,
            }
        )
        self.bridge.saveState(current)

        snapshot = self.bridge.deleteGesture("pending")

        self.assertNotIn(
            "pending",
            {gesture["gestureId"] for gesture in snapshot["gestures"]},
        )


if __name__ == "__main__":
    unittest.main()
