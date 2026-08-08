import tempfile
import unittest
from pathlib import Path

from app.bridges.session_bridge import SessionBridge, SessionState
from app.bridges.state_bridge import StateBridge
from app.core.camera_manager import CameraManager
from app.gestures.gesture_matcher import GestureMatcher
from app.gestures.gesture_store import GestureStore
from app.profile_manager import PatientProfile, ProfileManager


class FakeSignal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)

    def emit(self, *args) -> None:
        for callback in self.callbacks:
            callback(*args)


class FakeCamera:
    _loaded_session_gestures = CameraManager._loaded_session_gestures
    _refresh_gesture_matcher_templates = (
        CameraManager._refresh_gesture_matcher_templates
    )
    session_gesture_mappings = CameraManager.session_gesture_mappings
    configure_session_gestures = CameraManager.configure_session_gestures
    clear_session_gestures = CameraManager.clear_session_gestures

    def __init__(self, gestures_dir: Path) -> None:
        self.cameraStarted = FakeSignal()
        self.cameraStopped = FakeSignal()
        self.errorOccurred = FakeSignal()
        self.frameProcessed = FakeSignal()
        self.gestureMatchUpdated = FakeSignal()
        self.previewAspectRatioChanged = FakeSignal()
        self.gesture_matcher = GestureMatcher(gestures_dir)
        self.active_bridge = None
        self._loaded_session_gesture_ids = []
        self._session_key_bindings = {}
        self._use_session_gesture_subset = False

    def start(self, bridge: str) -> None:
        self.active_bridge = bridge
        self.cameraStarted.emit(bridge)

    def stop(self, bridge: str) -> None:
        if self.active_bridge != bridge:
            return
        self.active_bridge = None
        self.cameraStopped.emit(bridge)

    def openCameraSettings(self) -> None:
        pass


class SessionProfileFlowTests(unittest.TestCase):
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
        self.gesture_store.create_or_update(
            name="Left Arm Raise",
            regions=["upper_body"],
            active_joints=["R_SHOULDER_ABD"],
            target_angles={"R_SHOULDER_ABD": 90},
        )
        self.profile_manager.create(
            PatientProfile(
                patient_id="patient-a",
                patient_name="Patient A",
                key_bindings={
                    "right_arm_raise": "ArrowUp",
                    "missing_gesture": "M",
                },
            )
        )
        self.camera = FakeCamera(root / "gestures")
        self.bridge = SessionBridge(self.camera, self.profile_manager)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_load_profile_configures_only_bound_available_gestures(self) -> None:
        result = self.bridge.loadProfile("patient-a")

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["patientId"], "patient-a")
        self.assertEqual(
            result["data"]["gestures"],
            [
                {
                    "gestureId": "right_arm_raise",
                    "name": "Right Arm Raise",
                    "key": "ArrowUp",
                }
            ],
        )
        self.assertEqual(result["data"]["missingGestureIds"], ["missing_gesture"])
        self.assertEqual(
            self.camera.gesture_matcher.active_gesture_ids,
            frozenset({"right_arm_raise", "missing_gesture"}),
        )
        self.assertEqual(
            [
                template.gesture_id
                for template in self.camera.gesture_matcher._state_templates
            ],
            ["right_arm_raise"],
        )

    def test_start_session_emits_profile_key_with_match(self) -> None:
        matches = []
        # Avoid Qt Signal delivery (needs QApplication; CI may stub PySide6).
        self.bridge.gestureMatchUpdated = FakeSignal()
        self.bridge.gestureMatchUpdated.connect(matches.append)

        load_result = self.bridge.loadProfile("patient-a")
        self.bridge.startSession()
        self.camera.gestureMatchUpdated.emit(
            {
                "gestureId": "right_arm_raise",
                "name": "Right Arm Raise",
                "matched": True,
            }
        )

        self.assertTrue(load_result["ok"])
        self.assertEqual(self.bridge.state, SessionState.LIVE)
        self.assertEqual(matches[0]["key"], "ArrowUp")

    def test_start_session_without_profile_still_starts_camera(self) -> None:
        self.bridge.startSession()

        self.assertEqual(self.bridge.state, SessionState.LIVE)
        self.assertEqual(self.camera.active_bridge, "session")
        self.assertIsNone(self.bridge.active_patient_id)

    def test_stop_session_clears_profile_gesture_subset(self) -> None:
        self.bridge.loadProfile("patient-a")
        self.bridge.startSession()

        self.bridge.stopSession()

        self.assertEqual(self.bridge.state, SessionState.IDLE)
        self.assertIsNone(self.bridge.active_patient_id)
        self.assertEqual(self.camera._loaded_session_gesture_ids, [])
        self.assertFalse(self.camera._use_session_gesture_subset)

    def test_missing_profile_returns_error_without_starting_session(self) -> None:
        result = self.bridge.loadProfile("missing")

        self.assertFalse(result["ok"])
        self.assertEqual(self.bridge.state, SessionState.ERROR)
        self.assertIsNone(self.camera.active_bridge)


class StateDrivenFakeCamera:
    def __init__(self) -> None:
        self.cameraStarted = FakeSignal()
        self.cameraStopped = FakeSignal()
        self.errorOccurred = FakeSignal()
        self.previewFrameReady = FakeSignal()
        self.frameProcessed = FakeSignal()
        self.gestureMatchUpdated = FakeSignal()
        self.previewAspectRatioChanged = FakeSignal()
        self.active_bridge = None
        self.runtime_configuration = None

    def configure_runtime(self, configuration) -> None:
        self.runtime_configuration = configuration

    def start(self, bridge: str) -> None:
        self.active_bridge = bridge
        self.cameraStarted.emit(bridge)

    def stop(self, bridge: str) -> None:
        if self.active_bridge != bridge:
            return
        self.active_bridge = None
        self.cameraStopped.emit(bridge)


class StateDrivenSessionProfileFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.profile_manager = ProfileManager(root / "profiles")
        self.gesture_store = GestureStore(root / "gestures")
        self.gesture_store.create_or_update(
            gesture_id="right_arm_raise",
            name="Right Arm Raise",
            regions=["upper_body"],
            active_joints=["L_SHOULDER_ABD"],
            target_angles={"L_SHOULDER_ABD": 90},
        )
        self.state_bridge = StateBridge(
            root,
            self.gesture_store,
            self.profile_manager,
        )
        profile = self.profile_manager.load("patient-a")
        profile.key_bindings = {
            "right_arm_raise": "ArrowUp",
            "missing_gesture": "M",
        }
        self.profile_manager.save(profile)
        self.camera = StateDrivenFakeCamera()
        self.state_bridge.runtimeConfigurationChanged.connect(
            self.camera.configure_runtime
        )
        self.bridge = SessionBridge(self.camera, self.state_bridge)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_selected_profile_drives_runtime_and_session_mapping(self) -> None:
        result = self.bridge.loadProfile("patient-a")
        self.bridge.startSession()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["patientId"], "patient-a")
        self.assertEqual(
            result["data"]["gestures"],
            [
                {
                    "gestureId": "right_arm_raise",
                    "name": "Right Arm Raise",
                    "key": "ArrowUp",
                }
            ],
        )
        self.assertEqual(result["data"]["missingGestureIds"], ["missing_gesture"])
        self.assertEqual(
            self.camera.runtime_configuration["bindings"],
            {
                "right_arm_raise": "ArrowUp",
                "missing_gesture": "M",
            },
        )
        self.assertEqual(self.bridge.state, SessionState.LIVE)
        self.assertEqual(
            self.bridge.getLoadedSessionGestures()[0]["gestureId"],
            "right_arm_raise",
        )


if __name__ == "__main__":
    unittest.main()
