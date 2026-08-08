import unittest

from backend.matching_engine import AngleKey

from app.core.camera_manager import CameraManager


class FakeSignal:
    def __init__(self) -> None:
        self.emissions = []

    def emit(self, *args) -> None:
        self.emissions.append(args)


class FakeGestureSession:
    def __init__(self) -> None:
        self.active_angle_keys = frozenset({AngleKey.L_ELBOW})
        self.bound_angle_keys = {AngleKey.L_ELBOW}
        self.received_pose = None
        self.received_keys = None
        self.runtime_configuration = None
        self.stop_count = 0

    def process_pose(self, pose, keys, *, inject_keys):
        self.received_pose = pose
        self.received_keys = keys
        self.inject_keys = inject_keys
        return (
            {
                "gestureId": "left_arm",
                "name": "Left arm",
                "score": 0.9,
                "timestamp": 1.0,
                "matched": True,
                "hasTemplates": True,
                "gestureType": "state",
                "threshold": 0.64,
            },
            {AngleKey.L_ELBOW: 90.0},
        )

    def configure_runtime(self, bindings, settings, match_thresholds) -> None:
        self.runtime_configuration = (bindings, settings, match_thresholds)

    def stop(self) -> None:
        self.stop_count += 1

    @staticmethod
    def reset_match_payload():
        return {"keyAction": "reset"}


class RuntimeHarness:
    def __init__(self) -> None:
        self.active_bridge = "session"
        self.gestureMatchUpdated = FakeSignal()
        self.frameProcessed = FakeSignal()
        self.pose_pipeline = FakePosePipeline()
        self.gesture_session = FakeGestureSession()
        self.camera_session = FakeCameraSession()
        self._pending_pose_frame = FakeFrame()
        self._pending_pose_timestamp_ms = 321


class FakeFrame:
    @staticmethod
    def isNull() -> bool:
        return False


class FakeCameraSession:
    active = True


class FakePosePipeline:
    def __init__(self) -> None:
        self.models = []

    def configure_model(self, model) -> None:
        self.models.append(model)

    def clear_pending(self) -> None:
        pass


class FakePose:
    def __init__(self) -> None:
        self.xyz = [[0.1, 0.2, 0.3]]
        self.visibility = [0.95]


class FakeCalibrationCapture:
    def __init__(self) -> None:
        self.reset_count = 0

    def cancel(self) -> None:
        self.reset_count += 1


class ErrorHarness:
    def __init__(self) -> None:
        self.active_bridge = "calibrate"
        self.camera_session = FakeCameraSession()
        self.pose_pipeline = FakePosePipeline()
        self._pending_pose_frame = FakeFrame()
        self._pending_pose_timestamp_ms = 123
        self.calibration = FakeCalibrationCapture()
        self.gesture_session = FakeGestureSession()
        self.errorOccurred = FakeSignal()


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

        self.assertEqual(camera.gesture_session.stop_count, 0)
        self.assertEqual(
            camera.gesture_session.runtime_configuration,
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
            camera.gestureMatchUpdated.emissions[0][0]["keyAction"],
            "reset",
        )
        self.assertEqual(camera.pose_pipeline.models, ["lite"])

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
            camera.pose_pipeline.models,
            ["heavy", "lite"],
        )

    def test_pose_payload_keeps_raw_matching_data_timestamp_and_arm_filter(self) -> None:
        camera = RuntimeHarness()
        pose = FakePose()

        CameraManager.handle_pose_estimated(camera, pose, FakeFrame(), 321)

        self.assertIs(camera.gesture_session.received_pose, pose)
        self.assertEqual(
            camera.gesture_session.received_keys,
            frozenset({AngleKey.L_ELBOW}),
        )
        self.assertTrue(camera.gesture_session.inject_keys)
        _frame, payload = camera.frameProcessed.emissions[0]
        self.assertIs(payload["landmarks"], pose.xyz)
        self.assertEqual(payload["timestampMs"], 321)
        self.assertEqual(payload["renderJoints"], ["L_ELBOW"])

    def test_camera_error_cancels_an_in_progress_calibration_rep(self) -> None:
        camera = ErrorHarness()

        CameraManager.handle_camera_error(camera, "camera failed", "calibrate")

        self.assertEqual(camera.calibration.reset_count, 1)
        self.assertEqual(camera.gesture_session.stop_count, 1)
        self.assertEqual(
            camera.errorOccurred.emissions,
            [("camera failed", "calibrate")],
        )

if __name__ == "__main__":
    unittest.main()
