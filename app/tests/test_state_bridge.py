import tempfile
import unittest
from pathlib import Path

from app.gesture_store import GestureStore
from app.profile_manager import ProfileManager
from app.state_bridge import StateBridge


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
        current["bindings"] = [
            {"gestureId": "elbow", "key": "W", "matchThreshold": 63}
        ]

        saved = self.bridge.saveState(current)
        runtime = self.bridge.runtime_configuration()

        self.assertEqual(saved["bindings"][0]["matchThreshold"], 63)
        self.assertEqual(runtime["bindings"], {"elbow": "W"})
        self.assertEqual(runtime["matchThresholds"], {"elbow": 63})

    def test_legacy_binding_uses_global_threshold_as_its_default(self):
        current = self.bridge.getState()
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

    def test_delete_selected_profile_selects_remaining_profile(self):
        current = self.bridge.getState()
        selected_id = current["selectedPatientId"]

        updated = self.bridge.deleteProfile(selected_id)

        self.assertNotEqual(updated["selectedPatientId"], selected_id)
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
        gesture_store.create_or_update(
            gesture_id="delete_me",
            name="Delete Me",
            regions=["right_arm"],
            active_joints=["R_ELBOW"],
            target_angles={"R_ELBOW": 90.0},
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
