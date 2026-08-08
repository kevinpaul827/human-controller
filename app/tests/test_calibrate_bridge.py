import unittest

from app.bridges.calibration_bridge import CalibrateBridge


class FakeSignal:
    def connect(self, _callback) -> None:
        pass


class FakeCamera:
    def __init__(self) -> None:
        self.cameraStarted = FakeSignal()
        self.cameraStopped = FakeSignal()
        self.errorOccurred = FakeSignal()
        self.frameProcessed = FakeSignal()
        self.calibrationUpdated = FakeSignal()
        self.previewAspectRatioChanged = FakeSignal()
        self.saved = []

    def save_rep(self, name, gesture_id=None):
        self.saved.append((name, gesture_id))
        return {"gestureId": gesture_id or "generated", "name": name}

    @staticmethod
    def list_saved_gestures():
        return [{"gestureId": "saved", "name": "Saved"}]

    @staticmethod
    def loaded_session_gestures():
        return [{"gestureId": "loaded", "name": "Loaded"}]

    @staticmethod
    def load_saved_gesture(gesture_id):
        return {"gesture": {"gestureId": gesture_id, "name": "Loaded"}}


class FakeGestureStore:
    @staticmethod
    def list_gestures():
        return [{"gestureId": "from-store", "name": "From Store"}]


class CalibrateBridgeCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.camera = FakeCamera()
        self.bridge = CalibrateBridge(self.camera)

    def test_save_rep_supports_legacy_and_re_record_signatures(self) -> None:
        legacy = self.bridge.saveRep("Legacy")
        replacement = self.bridge.saveRep("Replacement", "same_id")

        self.assertEqual(legacy["gestureId"], "generated")
        self.assertEqual(replacement["gestureId"], "same_id")
        self.assertEqual(
            self.camera.saved,
            [("Legacy", None), ("Replacement", "same_id")],
        )

    def test_saved_gesture_compatibility_methods_delegate_to_camera(self) -> None:
        self.assertEqual(
            self.bridge.listSavedGestures(),
            [{"gestureId": "saved", "name": "Saved"}],
        )
        self.assertEqual(
            self.bridge.getLoadedSessionGestures(),
            [{"gestureId": "loaded", "name": "Loaded"}],
        )
        self.assertEqual(
            self.bridge.loadSavedGesture("saved")["gesture"]["gestureId"],
            "saved",
        )

    def test_saved_gesture_listing_uses_injected_store(self) -> None:
        bridge = CalibrateBridge(self.camera, FakeGestureStore())

        self.assertEqual(
            bridge.listSavedGestures(),
            [{"gestureId": "from-store", "name": "From Store"}],
        )


if __name__ == "__main__":
    unittest.main()
