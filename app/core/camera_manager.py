"""camera_manager.py

Coordinate camera capture, pose processing,
gesture matching, and calibration."
"""

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

from backend.perception.models import normalize_pose_model

from ..bridges.bridge_types import PosePayload
from ..calibration.calibration_service import CalibrationService
from ..platforms.system_settings import open_accessibility_settings, open_camera_settings
from ..utils.logging_utils import log_debug, log_info, log_verbose
from .camera_session import CameraSession
from .gesture_session import GestureSession
from .pose_pipeline import PosePipeline
from .runtime_configuration import RuntimeConfiguration


class CameraManager(QObject):
    cameraStarted = Signal(str)
    cameraStopped = Signal(str)
    errorOccurred = Signal(str, str)

    previewFrameReady = Signal(QImage, int)
    frameProcessed = Signal(QImage, dict)
    gestureMatchUpdated = Signal(dict)
    calibrationUpdated = Signal(dict)
    previewAspectRatioChanged = Signal(float)

    def __init__(self, gestures_dir=None, key_injector=None):
        super().__init__()
        self._frame_log_emitted = False
        self._preview_aspect_ratio = 4 / 3

        self.gesture_session = GestureSession(gestures_dir, key_injector)
        self.calibration = CalibrationService(
            self.gesture_session.store,
            on_update=self.calibrationUpdated.emit,
        )
        self.camera_session = CameraSession(self)
        self.camera_session.cameraStarted.connect(self.handle_camera_started)
        self.camera_session.cameraStopped.connect(self.handle_camera_stopped)
        self.camera_session.errorOccurred.connect(self.handle_camera_error)
        self.camera_session.frameReady.connect(self.handle_video_frame)
        self.pose_pipeline = PosePipeline(self)
        self.pose_pipeline.poseReady.connect(self.handle_pose_estimated)
        self.pose_pipeline.errorOccurred.connect(self.handle_pose_error)

    @property
    def active_bridge(self):
        return self.camera_session.active_bridge

    def start(self, bridge):
        self.camera_session.start(bridge)

    def stop(self, bridge):
        if self.active_bridge != bridge:
            return
        self.camera_session.stop()

    def handle_camera_started(self, bridge):
        self.gesture_session.start()
        self._frame_log_emitted = False
        self.pose_pipeline.clear_pending()
        self.cameraStarted.emit(bridge)

    @Slot("QVariantMap")
    def configure_runtime(self, configuration):
        runtime = RuntimeConfiguration.from_payload(configuration)
        settings = runtime.settings
        self.pose_pipeline.configure_model(
            normalize_pose_model(settings.get("poseModel"))
        )
        self._emit_runtime_reset_match()
        self.gesture_session.configure_runtime(
            runtime.bindings,
            settings,
            runtime.match_thresholds,
        )

    def handle_camera_stopped(self, bridge):
        CameraManager._reset_processing(self)
        self.cameraStopped.emit(bridge)

    def handle_camera_error(self, message, bridge):
        CameraManager._reset_processing(self)
        self.errorOccurred.emit(message, bridge)

    def _reset_processing(self):
        self.gesture_session.stop()
        self.calibration.cancel()
        self.pose_pipeline.clear_pending()

    def handle_video_frame(self, image, timestamp_ms):
        aspect_ratio = (
            image.width() / image.height()
            if image.height() > 0
            else self._preview_aspect_ratio
        )
        if abs(aspect_ratio - self._preview_aspect_ratio) > 0.001:
            self._preview_aspect_ratio = aspect_ratio
            log_debug(
                "[camera_manager] preview aspect ratio updated to "
                f"{aspect_ratio:.4f}"
            )
            self.previewAspectRatioChanged.emit(aspect_ratio)

        self.previewFrameReady.emit(image.copy(), int(timestamp_ms))

        if not self.pose_pipeline.submit(image, timestamp_ms):
            return

        if not self._frame_log_emitted:
            log_debug(
                f"[camera_manager] received first frame {image.width()}x{image.height()} at {timestamp_ms}ms"
            )
            self._frame_log_emitted = True

    def handle_pose_estimated(self, pose, frame, timestamp_ms):
        if not self.camera_session.active or self.active_bridge is None:
            return

        try:
            active_angle_keys = (
                self.gesture_session.active_angle_keys
                if self.active_bridge == "session"
                else None
            )
            match_payload, angles = self.gesture_session.process_pose(
                pose,
                active_angle_keys,
                inject_keys=self.active_bridge == "session",
            )
            if self.active_bridge == "calibrate":
                self.calibration.add_pose_angles(angles)
            self.gestureMatchUpdated.emit(match_payload)
        except Exception as error:
            log_info(f"[camera_manager] gesture matcher error: {error}")

        payload = self._pose_payload(pose, timestamp_ms)
        self.frameProcessed.emit(frame, payload)

    def handle_pose_error(self, message):
        log_info(f"[camera_manager] pose processor error: {message}")
        self.camera_session.emit_camera_error(message)

    def _emit_runtime_reset_match(self):
        if self.active_bridge != "session":
            return

        self.gestureMatchUpdated.emit(self.gesture_session.reset_match_payload())

    def _pose_payload(self, pose, timestamp_ms) -> PosePayload:
        if pose is None:
            log_verbose("[camera_manager] pose not detected")
            return {
                "detected": False,
                "landmarks": [],
                "visibility": [],
                "timestampMs": timestamp_ms,
            }

        log_verbose("[camera_manager] pose detected, forwarding live landmarks")
        payload: PosePayload = {
            "detected": True,
            "landmarks": pose.xyz,
            "visibility": pose.visibility,
            "timestampMs": timestamp_ms,
        }
        if self.active_bridge == "session":
            payload["renderJoints"] = sorted(
                joint.value for joint in self.gesture_session.bound_angle_keys
            )
        return payload

    def list_saved_gestures(self):
        return self.gesture_session.list_saved_gestures()

    def loaded_session_gestures(self):
        return self.gesture_session.loaded_gesture_summaries()

    def session_gesture_mappings(self):
        return self.gesture_session.gesture_mappings()

    def configure_session_gestures(self, key_bindings):
        return self.gesture_session.configure_gestures(key_bindings)

    def clear_session_gestures(self):
        self.gesture_session.clear_gestures()

    def load_saved_gesture(self, gesture_id):
        return self.gesture_session.load_saved_gesture(gesture_id)

    def start_calibration(self):
        self.calibration.start_calibration()

    def start_rep(self, recording_seconds=10.0):
        if self.active_bridge != "calibrate" or not self.camera_session.active:
            raise ValueError("Wait for the camera to be ready before recording.")
        self.calibration.start_rep(recording_seconds)

    def cancel_rep(self):
        self.calibration.cancel_rep()

    def stop_rep(self):
        return self.calibration.stop_rep()

    def reset_rep(self):
        self.calibration.reset_reps()

    def save_rep(self, name, gesture_id=None):
        result = self.calibration.save_rep(name, gesture_id)
        self.gesture_session.refresh_templates()
        return {**result, "loadedGestures": self.loaded_session_gestures()}

    @Slot()
    def openCameraSettings(self):
        if not open_camera_settings():
            self.camera_session.emit_camera_error(
                "Open your system camera privacy settings to allow access."
            )

    @Slot()
    def openAccessibilitySettings(self):
        if not open_accessibility_settings():
            self.camera_session.emit_camera_error(
                "Open your system accessibility settings to allow keyboard control."
            )

    @Slot()
    def shutdown(self):
        self.camera_session.stop()

        self.pose_pipeline.shutdown()
