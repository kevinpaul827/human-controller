import tempfile
import unittest
from pathlib import Path

from app.camera_manager import CameraManager
from app.gesture_matcher import GestureMatcher
from backend.matching_engine import AngleKey, TemplateBuilder


class FakeSignal:
    def __init__(self) -> None:
        self.emissions = []

    def emit(self, *args) -> None:
        self.emissions.append(args)


class FakeTriggerController:
    def __init__(self) -> None:
        self.settings = {"matchThreshold": 75.0}
        self.configuration = None

    def configure(self, bindings, settings, match_thresholds) -> None:
        self.configuration = (bindings, settings, match_thresholds)
        self.settings = {
            "matchThreshold": float(settings.get("matchThreshold", 75.0))
        }

    def process(self, _payload):
        return None

    def reset(self) -> None:
        pass


class FakeGestureMatcher:
    def __init__(self) -> None:
        self.active_configuration = None
        self.match_threshold = 0.0
        self.active_angle_keys = frozenset({AngleKey.L_ELBOW})
        self.bound_angle_keys = {AngleKey.L_ELBOW}
        self.received_pose = None
        self.received_keys = None

    def set_active_gestures(self, gesture_ids, thresholds) -> None:
        self.active_configuration = (list(gesture_ids), thresholds)

    def angles_for_pose(self, pose, keys):
        self.received_pose = pose
        self.received_keys = keys
        return {AngleKey.L_ELBOW: 90.0}

    def match_pose(self, _pose, *, angles):
        class Match:
            @staticmethod
            def to_dict():
                return {
                    "gestureId": "left_arm",
                    "name": "Left arm",
                    "score": 0.9,
                    "timestamp": 1.0,
                    "matched": True,
                    "hasTemplates": True,
                    "gestureType": "state",
                    "threshold": 0.64,
                }

        self.received_angles = angles
        return Match()


class RuntimeHarness:
    def __init__(self) -> None:
        self.active_bridge = "session"
        self.gestureMatchUpdated = FakeSignal()
        self.frameProcessed = FakeSignal()
        self.configurePoseModel = FakeSignal()
        self.trigger_controller = FakeTriggerController()
        self.gesture_matcher = FakeGestureMatcher()
        self.release_count = 0
        self._active = True
        self._pending_pose_frame = FakeFrame()
        self._pending_pose_timestamp_ms = 321

    def _release_injected_keys(self) -> None:
        self.release_count += 1


class FakeFrame:
    @staticmethod
    def isNull() -> bool:
        return False


class FakePose:
    def __init__(self) -> None:
        self.xyz = [[0.1, 0.2, 0.3]]
        self.visibility = [0.95]


class FakeCalibrationCapture:
    def __init__(self) -> None:
        self.reset_count = 0

    def reset(self) -> None:
        self.reset_count += 1

    def cancel(self) -> None:
        self.reset_count += 1


class ErrorHarness:
    def __init__(self) -> None:
        self.active_bridge = "calibrate"
        self._active = True
        self._stopping = False
        self._pending_pose_frame = FakeFrame()
        self._pending_pose_timestamp_ms = 123
        self._recording_rep = True
        self.calibration_capture = FakeCalibrationCapture()
        self.trigger_controller = FakeTriggerController()
        self.errorOccurred = FakeSignal()
        self.release_count = 0

    def _release_injected_keys(self) -> None:
        self.release_count += 1

    def release_camera(self) -> None:
        pass


class CalibrationHarness:
    _refresh_gesture_matcher_templates = (
        CameraManager._refresh_gesture_matcher_templates
    )
    _loaded_session_gestures = CameraManager._loaded_session_gestures
    loaded_session_gestures = CameraManager.loaded_session_gestures

    def __init__(self, gestures_dir: Path) -> None:
        self.gesture_matcher = GestureMatcher(gestures_dir)
        self.template_builder = TemplateBuilder()
        self._loaded_session_gesture_ids = []
        self._session_key_bindings = {}
        self._use_session_gesture_subset = False
        self._calibration_frames = []
        self._calibration_reps = []
        self._recording_rep = False
        self.calibration_capture = FakeCalibrationCapture()
        self.update_count = 0

    def _emit_calibration_updated(self) -> None:
        self.update_count += 1


class CameraManagerRuntimeTests(unittest.TestCase):
    def test_runtime_configuration_filters_bindings_and_clears_held_ui(self) -> None:
        camera = RuntimeHarness()

        CameraManager.configure_runtime(
            camera,
            {
                "bindings": {"left_arm": "A"},
                "matchThresholds": {"left_arm": 64},
                "settings": {"matchThreshold": 72},
            },
        )

        self.assertEqual(camera.release_count, 1)
        self.assertEqual(camera._loaded_session_gesture_ids, ["left_arm"])
        self.assertEqual(camera._session_key_bindings, {"left_arm": "A"})
        self.assertEqual(
            camera.trigger_controller.configuration,
            (
                {"left_arm": "A"},
                {
                    "matchThreshold": 72.0,
                    "holdDuration": 1.5,
                    "cooldown": 0.5,
                    "smoothing": 2,
                    "poseModel": "lite",
                },
                {"left_arm": 64.0},
            ),
        )
        self.assertEqual(
            camera.gesture_matcher.active_configuration,
            (["left_arm"], {"left_arm": 0.64}),
        )
        self.assertEqual(camera.gesture_matcher.match_threshold, 0.72)
        self.assertEqual(
            camera.gestureMatchUpdated.emissions[0][0]["keyAction"],
            "reset",
        )
        self.assertEqual(camera.configurePoseModel.emissions, [("lite",)])

    def test_runtime_configuration_selects_and_normalizes_pose_model(self) -> None:
        camera = RuntimeHarness()

        CameraManager.configure_runtime(
            camera,
            {
                "bindings": {},
                "matchThresholds": {},
                "settings": {"matchThreshold": 75, "poseModel": "HEAVY"},
            },
        )
        CameraManager.configure_runtime(
            camera,
            {
                "bindings": {},
                "matchThresholds": {},
                "settings": {"matchThreshold": 75, "poseModel": "unknown"},
            },
        )

        self.assertEqual(
            camera.configurePoseModel.emissions,
            [("heavy",), ("lite",)],
        )

    def test_pose_payload_keeps_raw_matching_data_timestamp_and_arm_filter(self) -> None:
        camera = RuntimeHarness()
        pose = FakePose()

        CameraManager.handle_pose_estimated(camera, pose)

        self.assertIs(camera.gesture_matcher.received_pose, pose)
        self.assertEqual(
            camera.gesture_matcher.received_keys,
            frozenset({AngleKey.L_ELBOW}),
        )
        self.assertEqual(
            camera.gesture_matcher.received_angles,
            {AngleKey.L_ELBOW: 90.0},
        )
        _frame, payload = camera.frameProcessed.emissions[0]
        self.assertIs(payload["landmarks"], pose.xyz)
        self.assertEqual(payload["timestampMs"], 321)
        self.assertEqual(payload["renderJoints"], ["L_ELBOW"])

    def test_camera_error_cancels_an_in_progress_calibration_rep(self) -> None:
        camera = ErrorHarness()

        CameraManager.emit_camera_error(camera, "camera failed")

        self.assertFalse(camera._recording_rep)
        self.assertEqual(camera.calibration_capture.reset_count, 1)
        self.assertIsNone(camera.active_bridge)
        self.assertEqual(
            camera.errorOccurred.emissions,
            [("camera failed", "calibrate")],
        )

    def test_save_rep_keeps_static_and_motion_templates_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            camera = CalibrationHarness(Path(temp_dir))
            camera._calibration_reps = [{AngleKey.L_ELBOW: 90.0}]

            static_result = CameraManager.save_rep(
                camera,
                "Held elbow",
                "held_elbow",
            )
            static_gesture = camera.gesture_matcher.store.load("held_elbow")

            self.assertEqual(static_result["gestureId"], "held_elbow")
            self.assertEqual(static_gesture.type, "state")
            self.assertEqual(static_gesture.trajectory, [])

            camera._calibration_reps = [
                [
                    {AngleKey.L_ELBOW: 60.0},
                    {AngleKey.L_ELBOW: 100.0},
                    {AngleKey.L_ELBOW: 150.0},
                ]
            ]
            motion_result = CameraManager.save_rep(
                camera,
                "Elbow sweep",
                "elbow_sweep",
            )
            motion_gesture = camera.gesture_matcher.store.load("elbow_sweep")

            self.assertEqual(motion_result["gestureId"], "elbow_sweep")
            self.assertEqual(motion_gesture.type, "motion")
            self.assertEqual(len(motion_gesture.trajectory), 32)


if __name__ == "__main__":
    unittest.main()
