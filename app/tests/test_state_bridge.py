import tempfile
import unittest
from pathlib import Path

from app.gesture_store import GestureStore
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
        created = self.bridge.createProfile("New Patient")
        profile = next(
            item
            for item in created["patients"]
            if item["patientName"] == "New Patient"
        )

        self.assertEqual(created["selectedPatientId"], profile["patientId"])


if __name__ == "__main__":
    unittest.main()
