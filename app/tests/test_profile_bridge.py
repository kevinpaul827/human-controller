import json
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from app.gesture_store import GestureStore
from app.profile_bridge import ProfileBridge
from app.profile_manager import ProfileManager


class ProfileBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.profile_manager = ProfileManager(root / "profiles")
        self.gesture_store = GestureStore(root / "gestures")
        self.gesture_store.create_or_update(
            name="Right Arm Raise",
            regions=["upper_body"],
            active_joints=["L_SHOULDER_ABD"],
            target_angles={"L_SHOULDER_ABD": 90},
        )
        self.bridge = ProfileBridge(self.profile_manager, self.gesture_store)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _response(self, raw_response: str) -> dict:
        return json.loads(raw_response)

    def test_profile_crud_and_key_bindings(self) -> None:
        created = self._response(self.bridge.createProfile("Patient A", "Demo notes"))
        self.assertTrue(created["ok"])
        self.assertEqual(created["data"]["keyBindings"], {})
        patient_id = created["data"]["patientId"]
        self.assertEqual(str(UUID(patient_id)), patient_id)

        updated = self._response(
            self.bridge.setKeyBinding(
                patient_id,
                "right_arm_raise",
                "ArrowUp",
            )
        )
        self.assertTrue(updated["ok"])
        self.assertEqual(
            updated["data"]["keyBindings"]["right_arm_raise"],
            "ArrowUp",
        )

        removed = self._response(
            self.bridge.removeKeyBinding(patient_id, "right_arm_raise")
        )
        self.assertTrue(removed["ok"])
        self.assertEqual(removed["data"]["keyBindings"], {})

        deleted = self._response(self.bridge.deleteProfile(patient_id))
        self.assertEqual(deleted, {"ok": True, "data": patient_id})

    def test_lists_profiles_and_user_facing_gesture_names(self) -> None:
        self.bridge.createProfile("Patient A", "")

        profiles = self._response(self.bridge.listProfiles())
        gestures = self._response(self.bridge.listGestures())

        self.assertEqual(profiles["data"][0]["patientName"], "Patient A")
        self.assertEqual(gestures["data"][0]["name"], "Right Arm Raise")
        self.assertEqual(gestures["data"][0]["gestureId"], "right_arm_raise")
        self.assertEqual(gestures["data"][0]["type"], "state")

    def test_returns_error_response_for_invalid_profile(self) -> None:
        response = self._response(self.bridge.createProfile("", ""))

        self.assertFalse(response["ok"])
        self.assertIn("patient_name", response["error"])

    def test_mutations_emit_profiles_changed(self) -> None:
        changes = []
        self.bridge.profilesChanged.connect(lambda: changes.append(True))

        created = self._response(self.bridge.createProfile("Patient A", ""))["data"]
        self.bridge.setKeyBinding(created["patientId"], "arm_raise", "A")
        self.bridge.removeKeyBinding(created["patientId"], "arm_raise")
        self.bridge.deleteProfile(created["patientId"])

        self.assertEqual(len(changes), 4)


if __name__ == "__main__":
    unittest.main()
