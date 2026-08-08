import sys
import time
from typing import cast

from PySide6.QtCore import QCameraPermission, QCoreApplication, QElapsedTimer, QObject, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QImage
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices, QVideoFrame, QVideoSink

from backend.matching_engine import AngleKey, TemplateBuilder
from backend.matching_engine.core.angles import reduce_joints
from backend.perception.models import normalize_pose_model

from .bridge_types import CalibrationUpdatePayload, GestureMatchPayload, PosePayload
from .calibration_capture import CalibrationCaptureController, CapturePhase
from .gesture_matcher import GestureMatcher
from .gesture_regions import infer_gesture_regions
from .gesture_store import SavedGesture
from .key_injector import KeyInjectionError, KeyInjector
from .logging_utils import log_debug, log_info, log_verbose
from .pose_processor import PoseProcessor
from .runtime_configuration import RuntimeConfiguration
from .trigger_controller import TriggerController

# CameraManager handles both calibration and live camera sessions.
# It starts/stops the camera, processes video frames, and sends events for the UI.
#
# Calibration methods:
# - start_calibration: begin collecting pose frames for a new gesture.
# - capture_rep: save the current held pose as one repetition.
# - reset_rep: clear collected calibration data.
# - save_rep: save the captured reps as a new gesture.
#
# Session methods:
# - start: open the camera for a bridge and begin streaming.
# - stop: stop the camera when the bridge is done.
#
# Shared methods:
# - check_camera_permissions / create_camera / start_camera / stop_camera
# - handle_video_frame / handle_pose_estimated / emit_camera_error
class CameraManager(QObject):
    cameraStarted = Signal(str)
    cameraStopped = Signal(str)
    errorOccurred = Signal(str, str)

    previewFrameReady = Signal(QImage, int)
    frameProcessed = Signal(QImage, dict)
    gestureMatchUpdated = Signal(dict)
    calibrationUpdated = Signal(dict)
    previewAspectRatioChanged = Signal(float)
    processFrame = Signal(object, int)
    configurePoseModel = Signal(str)
    closePoseProcessor = Signal()

    def __init__(self, gestures_dir=None, key_injector=None):
        super().__init__()
        self.active_camera = None
        self.active_bridge = None
        self.camera_timer = QElapsedTimer()
        self.capture_session = None
        self.video_sink = QVideoSink(self)

        self._active = False
        self._stopping = False
        self._frame_log_emitted = False
        self._pending_pose_frame = QImage()
        self._pending_pose_timestamp_ms = -1
        self._preview_aspect_ratio = 4 / 3

        self.gesture_matcher = GestureMatcher(gestures_dir) if gestures_dir else GestureMatcher()
        self.key_injector = key_injector or KeyInjector()
        self.trigger_controller = TriggerController()
        log_info(f"gesture matcher file: {self.gesture_matcher.__class__.__module__}")
        log_info(f"has angles_for_pose: {hasattr(self.gesture_matcher, 'angles_for_pose')}")
        self.template_builder = TemplateBuilder()
        self._loaded_session_gesture_ids = []
        self._session_key_bindings = {}
        self._use_session_gesture_subset = False
        self._calibration_frames = []
        self._calibration_reps = []
        self._recording_rep = False
        self.calibration_capture = CalibrationCaptureController()
        self.pose_processing = False
        self.pose_thread = QThread(self)
        self.pose_processor = PoseProcessor()
        self.pose_processor.moveToThread(self.pose_thread)

        self.processFrame.connect(self.pose_processor.process_frame, Qt.ConnectionType.QueuedConnection)
        self.configurePoseModel.connect(
            self.pose_processor.configure_model,
            Qt.ConnectionType.QueuedConnection,
        )
        self.pose_processor.poseEstimated.connect(self.handle_pose_estimated)
        self.pose_processor.processingFinished.connect(self.handle_processing_finished)
        self.pose_processor.errorOccurred.connect(self.handle_pose_error)

        self.closePoseProcessor.connect(self.pose_processor.close, Qt.ConnectionType.BlockingQueuedConnection)
        self.pose_thread.finished.connect(self.pose_processor.deleteLater)
        self.video_sink.videoFrameChanged.connect(self.handle_video_frame)
        self.pose_thread.start()
    
    def start(self, bridge):
        if self._active and self.active_bridge == bridge:
            return
        
        if self.active_bridge is not None and self.active_bridge != bridge:
            self.stop_camera()
        
        self.active_bridge = bridge
        
        if self.check_camera_permissions():
            if self.create_camera():
                self.start_camera()
        
    def stop(self, bridge):
        if self.active_bridge != bridge:
            return
        
        self.stop_camera()

    def permission_denied_message(self):
        if sys.platform == "win32":
            return (
                "Camera access was denied by Windows. Enable camera access for desktop apps "
                "in Settings > Privacy & security > Camera."
            )

        if sys.platform == "darwin":
            return (
                "Camera access was denied by macOS. Check System Settings > Privacy & Security "
                "> Camera and confirm the app bundle includes NSCameraUsageDescription."
            )

        return "Camera permission denied."

    def check_camera_permissions(self):
        app = QCoreApplication.instance()
        permission = QCameraPermission()
        status = app.checkPermission(permission)

        if status == Qt.PermissionStatus.Granted:
            return True

        if status == Qt.PermissionStatus.Denied:
            self.emit_camera_error(self.permission_denied_message())
            return False

        app.requestPermission(permission, self, self.handle_request_camera)
        return False

    def create_camera(self):
        if self.active_camera is not None and self.capture_session is not None:
            return True

        video_input = QMediaDevices.defaultVideoInput()

        if video_input.isNull():
            self.emit_camera_error("No camera detected on this device.")
            return False

        self.release_camera()

        self.active_camera = QCamera(video_input, self)
        self.capture_session = QMediaCaptureSession()
        self.capture_session.setCamera(self.active_camera)
        self.capture_session.setVideoSink(self.video_sink)

        self.active_camera.activeChanged.connect(self.handle_active_changed)
        self.active_camera.errorOccurred.connect(self.handle_error_occurred)
        return True

    def start_camera(self):
        if self.active_bridge is None:
            return

        if self.active_camera is None:
            if not self.create_camera():
                return

        self._release_injected_keys()
        self._refresh_gesture_matcher_templates()
        self.trigger_controller.reset()
        self.camera_timer.restart()
        self._frame_log_emitted = False
        self._pending_pose_frame = QImage()
        self._pending_pose_timestamp_ms = -1
        log_info("[camera_manager] starting camera session")
        self.active_camera.start()

    @Slot("QVariantMap")
    def configure_runtime(self, configuration):
        runtime = RuntimeConfiguration.from_payload(configuration)
        self._release_injected_keys()
        settings = runtime.settings
        self.configurePoseModel.emit(normalize_pose_model(settings.get("poseModel")))
        CameraManager._emit_runtime_reset_match(self)
        bindings = runtime.bindings
        match_thresholds = runtime.match_thresholds
        CameraManager._apply_runtime_bindings(self, bindings)
        self.trigger_controller.configure(
            bindings,
            settings,
            match_thresholds,
        )
        self.gesture_matcher.set_active_gestures(
            bindings.keys(),
            {
                gesture_id: threshold / 100.0
                for gesture_id, threshold in match_thresholds.items()
            },
        )
        threshold = self.trigger_controller.settings["matchThreshold"] / 100.0
        self.gesture_matcher.match_threshold = threshold

    def stop_camera(self):
        log_info("[camera_manager] stopping camera session")
        stopping_bridge = CameraManager._deactivate_camera_session(self)
        if stopping_bridge is not None:
            self.cameraStopped.emit(stopping_bridge)
    
    def release_camera(self):
        if self.active_camera is not None:
            self.active_camera.stop()
            self.active_camera.deleteLater()
            self.active_camera = None
        
        if self.capture_session is not None:
            self.capture_session.setCamera(None)
            self.capture_session.setVideoSink(None)
            self.capture_session.deleteLater()
            self.capture_session = None
    
    def emit_camera_error(self, message):
        if self.active_bridge is None:
            return

        stopping_bridge = CameraManager._deactivate_camera_session(self)
        if stopping_bridge is not None:
            self.errorOccurred.emit(message, stopping_bridge)

    def handle_request_camera(self, permission):
        app = QCoreApplication.instance()

        if app.checkPermission(permission) == Qt.PermissionStatus.Granted:
            if self.active_bridge is None:
                return

            if self.create_camera():
                self.start_camera()
        else:
            self.emit_camera_error(self.permission_denied_message())

    def handle_active_changed(self, active):
        if active:
            if self._active:
                return
            
            self._active = True

            if self.active_bridge is not None:
                self.cameraStarted.emit(self.active_bridge)

            return
        
        if not self._active:
            return
        
        self._active = False

        if self._stopping:
            return

        self._release_injected_keys()
        self.trigger_controller.reset()
        self._recording_rep = False
        self.calibration_capture.cancel()

        stopping_bridge = self.active_bridge
        self.active_bridge = None
        if stopping_bridge is not None:
            self.cameraStopped.emit(stopping_bridge)

    def handle_error_occurred(self, error, error_message):
        if sys.platform == "win32":
            message = (
                error_message
                or "Windows blocked camera access. Check Privacy & security > Camera."
            )
        else:
            message = error_message or "Unable to start camera session."

        self.emit_camera_error(message)

    def handle_video_frame(self, video_frame: QVideoFrame):
        if not self._active or self.active_bridge is None:
            return

        image = video_frame.toImage()

        if image.isNull():
            log_debug("[camera_manager] skipped null video frame")
            return

        aspect_ratio = image.width() / image.height() if image.height() > 0 else self._preview_aspect_ratio
        if abs(aspect_ratio - self._preview_aspect_ratio) > 0.001:
            self._preview_aspect_ratio = aspect_ratio
            log_debug(f"[camera_manager] preview aspect ratio updated to {aspect_ratio:.4f}")
            self.previewAspectRatioChanged.emit(aspect_ratio)
        
        timestamp_ms = video_frame.startTime() // 1000

        if timestamp_ms < 0:
            timestamp_ms = self.camera_timer.elapsed()

        self.previewFrameReady.emit(image.copy(), int(timestamp_ms))

        if self.pose_processing:
            return

        if not self._frame_log_emitted:
            log_debug(
                f"[camera_manager] received first frame {image.width()}x{image.height()} at {timestamp_ms}ms"
            )
            self._frame_log_emitted = True

        self._pending_pose_frame = image.copy()
        self._pending_pose_timestamp_ms = int(timestamp_ms)
        self.pose_processing = True

        self.processFrame.emit(self._pending_pose_frame.copy(), int(timestamp_ms))

    def handle_pose_estimated(self, pose):
        if not self._active or self.active_bridge is None:
            self._pending_pose_frame = QImage()
            self._pending_pose_timestamp_ms = -1
            return

        if self._pending_pose_frame.isNull():
            return

        try:
            if hasattr(self.gesture_matcher, "angles_for_pose"):
                active_angle_keys = (
                    self.gesture_matcher.active_angle_keys
                    if self.active_bridge == "session"
                    else None
                )
                angles = self.gesture_matcher.angles_for_pose(
                    pose, active_angle_keys
                )
            elif hasattr(self.gesture_matcher, "feature_extractor") and hasattr(
                self.gesture_matcher.feature_extractor, "to_angles"
            ):
                angles = (
                    self.gesture_matcher.feature_extractor.to_angles(pose)
                    if pose is not None
                    else {}
                )
                log_info(
                    "[camera_manager] gesture matcher missing angles_for_pose; "
                    "using feature extractor fallback"
                )
            else:
                raise AttributeError(
                    "Gesture matcher is missing angles_for_pose and has no fallback "
                    "feature extractor."
                )

            # If we are in calibration mode, save the current pose angles
            # so the user can capture them later as a calibration rep.
            if self.active_bridge == "calibrate":
                self._append_calibration_frame(angles)
                if self._recording_rep:
                    captured = self.calibration_capture.update(
                        angles, time.monotonic()
                    )
                    if captured:
                        self._finalize_automatic_rep()
                    else:
                        self._emit_calibration_updated()
            match_event = self.gesture_matcher.match_pose(pose, angles=angles)
            match_payload = cast(GestureMatchPayload, match_event.to_dict())
            key_action = self.trigger_controller.process(match_payload)
            if key_action is not None and self.active_bridge == "session":
                try:
                    if key_action["action"] == "press":
                        self.key_injector.press(key_action["key"])
                        match_payload.update(
                            {
                                "triggered": True,
                                "key": key_action["key"],
                                "keyAction": "press",
                            }
                        )
                    else:
                        self.key_injector.release(key_action["key"])
                        match_payload.update(
                            {
                                "key": key_action["key"],
                                "keyAction": "release",
                            }
                        )
                except KeyInjectionError as error:
                    self._release_injected_keys()
                    self.trigger_controller.reset()
                    match_payload.update(
                        {
                            "triggered": False,
                            "key": key_action["key"],
                            "injectionError": str(error),
                        }
                    )
            self.gestureMatchUpdated.emit(match_payload)
        except Exception as error:
            log_info(f"[camera_manager] gesture matcher error: {error}")

        payload = CameraManager._pose_payload(self, pose)

        frame = self._pending_pose_frame
        self._pending_pose_frame = QImage()
        self._pending_pose_timestamp_ms = -1
        self.frameProcessed.emit(frame, payload)

    def handle_processing_finished(self):
        self.pose_processing = False

    def handle_pose_error(self, message):
        log_info(f"[camera_manager] pose processor error: {message}")
        self.emit_camera_error(message)

    def _release_injected_keys(self):
        try:
            self.key_injector.release_all()
        except KeyInjectionError as error:
            log_info(f"[camera_manager] failed to release injected key: {error}")

    def _emit_runtime_reset_match(self):
        if self.active_bridge != "session":
            return

        self.gestureMatchUpdated.emit(CameraManager._reset_match_payload(self))

    def _apply_runtime_bindings(self, bindings):
        self._session_key_bindings = bindings
        self._loaded_session_gesture_ids = list(bindings)
        self._use_session_gesture_subset = True

    def _reset_camera_runtime_state(self):
        self._release_injected_keys()
        self.trigger_controller.reset()
        self._active = False
        self._pending_pose_frame = QImage()
        self._pending_pose_timestamp_ms = -1
        self._recording_rep = False
        self.calibration_capture.cancel()

    def _deactivate_camera_session(self):
        self._stopping = True
        CameraManager._reset_camera_runtime_state(self)
        self.release_camera()
        stopping_bridge = self.active_bridge
        self.active_bridge = None
        self._stopping = False
        return stopping_bridge

    def _reset_match_payload(self) -> GestureMatchPayload:
        return {
            "gestureId": None,
            "name": None,
            "score": 0.0,
            "timestamp": None,
            "matched": False,
            "hasTemplates": False,
            "gestureType": None,
            "triggered": False,
            "keyAction": "reset",
        }

    def _pose_payload(self, pose) -> PosePayload:
        if pose is None:
            log_verbose("[camera_manager] pose not detected")
            return {
                "detected": False,
                "landmarks": [],
                "visibility": [],
                "timestampMs": self._pending_pose_timestamp_ms,
            }

        log_verbose("[camera_manager] pose detected, forwarding live landmarks")
        payload: PosePayload = {
            "detected": True,
            "landmarks": pose.xyz,
            "visibility": pose.visibility,
            "timestampMs": self._pending_pose_timestamp_ms,
        }
        if self.active_bridge == "session":
            payload["renderJoints"] = sorted(
                joint.value for joint in self.gesture_matcher.bound_angle_keys
            )
        return payload

############################## Calibration Methods #############################
    def _loaded_session_gestures(self):
        gestures = []
        for gesture_id in self._loaded_session_gesture_ids:
            try:
                gestures.append(self.gesture_matcher.store.load(gesture_id))
            except (OSError, ValueError, FileNotFoundError):
                continue
        return gestures

    def _refresh_gesture_matcher_templates(self):
        self.gesture_matcher.reload_templates()
        if self._use_session_gesture_subset:
            self.gesture_matcher.set_active_gestures(
                self._loaded_session_gesture_ids,
                self.gesture_matcher.match_thresholds,
            )
            return

        self.gesture_matcher.set_active_gestures(None)

    def list_saved_gestures(self):
        return self.gesture_matcher.store.list_gestures()

    def loaded_session_gestures(self):
        return [gesture.to_summary() for gesture in self._loaded_session_gestures()]

    def session_gesture_mappings(self):
        return [
            {
                **gesture.to_summary(),
                "key": self._session_key_bindings.get(gesture.gesture_id, ""),
            }
            for gesture in self._loaded_session_gestures()
        ]

    def configure_session_gestures(self, key_bindings):
        self._session_key_bindings = dict(key_bindings)
        self._loaded_session_gesture_ids = list(self._session_key_bindings)
        self._use_session_gesture_subset = True
        self._refresh_gesture_matcher_templates()
        return self.session_gesture_mappings()

    def clear_session_gestures(self):
        self._loaded_session_gesture_ids = []
        self._session_key_bindings = {}
        self._use_session_gesture_subset = False
        self._refresh_gesture_matcher_templates()

    def load_saved_gesture(self, gesture_id):
        resolved_gesture_id = str(gesture_id or "").strip()
        if not resolved_gesture_id:
            raise ValueError("Gesture ID is required.")

        gesture = self.gesture_matcher.store.load(resolved_gesture_id)
        if resolved_gesture_id not in self._session_key_bindings:
            raise ValueError(
                "Assign this movement a profile key binding before loading it "
                "for a session."
            )
        return {
            "gesture": gesture.to_summary(),
            "loadedGestures": self.loaded_session_gestures(),
        }

    def _append_calibration_frame(self, angles):
        if not angles:
            return
        self._calibration_frames.append(angles)

    def _emit_calibration_updated(self):
        now = time.monotonic()
        payload: CalibrationUpdatePayload = {
            "repCount": len(self._calibration_reps),
            "capturing": self._recording_rep,
            "phase": self.calibration_capture.phase.value,
            "countdownRemaining": self.calibration_capture.remaining_seconds(now),
        }
        self.calibrationUpdated.emit(payload)

    def _finalize_automatic_rep(self):
        frames = list(self.calibration_capture.frames)
        if not frames:
            self.calibration_capture.cancel()
            self._recording_rep = False
            self._emit_calibration_updated()
            return

        self._calibration_reps.append(frames)
        self._calibration_frames = []
        self._recording_rep = False
        self._emit_calibration_updated()

    def start_calibration(self):
        """Start a new calibration session.

        This clears any old pose frames and reps, and tells the UI that
        calibration has started.
        """
        self._calibration_frames = []
        self._calibration_reps = []
        self._recording_rep = False
        self.calibration_capture.reset()
        self._emit_calibration_updated()

    def start_rep(self, recording_seconds=10.0):
        if self.active_bridge != "calibrate" or not self._active:
            raise ValueError("Wait for the camera to be ready before recording.")
        self._calibration_frames = []
        self.calibration_capture.start(time.monotonic(), recording_seconds)
        self._recording_rep = True
        self._emit_calibration_updated()

    def cancel_rep(self):
        self._calibration_frames = []
        self._recording_rep = False
        self.calibration_capture.cancel()
        self._emit_calibration_updated()

    def stop_rep(self):
        if not self._recording_rep:
            raise ValueError("Start recording before stopping this rep.")
        self._recording_rep = False
        frames = list(self.calibration_capture.frames or self._calibration_frames)
        if not frames:
            self.calibration_capture.cancel()
            self._emit_calibration_updated()
            raise ValueError("Hold a pose first before capturing a rep.")

        self.calibration_capture.phase = CapturePhase.CAPTURED
        self._calibration_frames = frames
        result = self.capture_rep()
        self._calibration_reps[-1] = frames
        return result

    def capture_rep(self):
        """Capture the current held pose as one calibration rep.

        The method averages the saved pose frames for this rep and stores the
        result. It also clears the current capture frames so the next rep can be recorded.
        """
        if self._recording_rep:
            return self.stop_rep()
        if not self._calibration_frames:
            raise ValueError("Hold a pose first before capturing a rep.")

        snapshot = reduce_joints(list(self._calibration_frames), lambda values: sum(values) / len(values))
        self._calibration_reps.append(snapshot)
        self._calibration_frames = []
        self._emit_calibration_updated()
        return {
            "repCount": len(self._calibration_reps),
            "angles": {
                key.value: value
                for key, value in snapshot.items()
                if value is not None
            },
        }

    def reset_rep(self):
        """Reset the current calibration reps.

        This clears both the frames being collected for the current rep and all
        reps already captured in the session.
        """
        self._calibration_frames = []
        self._calibration_reps = []
        self._recording_rep = False
        self.calibration_capture.reset()
        self._emit_calibration_updated()

    def save_rep(self, name, gesture_id=None):
        """Save the captured reps as a new or re-recorded gesture template.

        The given name is required. Saved reps are converted into a gesture and
        stored for later matching.
        """
        resolved_name = str(name or "").strip()
        if not resolved_name:
            log_info("[camera_manager.save_rep] aborted: empty gesture name")
            raise ValueError("Gesture name is required.")
        if not self._calibration_reps:
            log_info("[camera_manager.save_rep] aborted: no captured reps available")
            raise ValueError("Capture at least one rep before saving.")

        motion_mode = any(
            isinstance(rep, list) for rep in self._calibration_reps
        )
        if motion_mode:
            reps = [
                rep if isinstance(rep, list) else [rep]
                for rep in self._calibration_reps
            ]
            template = self.template_builder.build(
                reps,
                name=resolved_name,
                mode="motion",
            )
        else:
            active_joints = [
                joint
                for joint in AngleKey
                if any(
                    rep.get(joint) is not None
                    for rep in self._calibration_reps
                )
            ]
            template = self.template_builder.build(
                [[rep] for rep in self._calibration_reps],
                name=resolved_name,
                active_joints=active_joints or None,
            )
        active_joint_names = [joint.value for joint in template.active_joints]
        saved = SavedGesture(
            gesture_id=str(gesture_id or template.gesture_id),
            name=template.name,
            type=template.type,
            regions=infer_gesture_regions(active_joint_names),
            active_joints=active_joint_names,
            target_angles={joint.value: float(value) for joint, value in template.target_angles.items()},
            tolerance_deg={joint.value: float(value) for joint, value in template.tolerance_deg.items()},
            trajectory=list(template.trajectory),
            fps=int(template.fps),
        )
        self.gesture_matcher.store.save(saved)
        self._refresh_gesture_matcher_templates()
        self._calibration_frames = []
        self._calibration_reps = []
        self._recording_rep = False
        self.calibration_capture.reset()
        self._emit_calibration_updated()
        return {
            "gestureId": saved.gesture_id,
            "name": saved.name,
            "repCount": 0,
            "loadedGestures": self.loaded_session_gestures(),
        }
################################################################################
    @Slot()
    def openCameraSettings(self):
        if sys.platform == "win32":
            QDesktopServices.openUrl(QUrl("ms-settings:privacy-webcam"))
            return

        if sys.platform == "darwin":
            QDesktopServices.openUrl(
                QUrl("x-apple.systempreferences:com.apple.preference.security?Privacy_Camera")
            )
            return

        self.emit_camera_error("Open your system camera privacy settings to allow access.")

    @Slot()
    def openAccessibilitySettings(self):
        if sys.platform == "darwin":
            QDesktopServices.openUrl(
                QUrl(
                    "x-apple.systempreferences:com.apple.preference.security?"
                    "Privacy_Accessibility"
                )
            )
            return

        self.emit_camera_error(
            "Open your system accessibility settings to allow keyboard control."
        )

    @Slot()
    def shutdown(self):
        self.stop_camera()

        if self.pose_thread.isRunning():
            self.closePoseProcessor.emit()
            self.pose_thread.quit()
            self.pose_thread.wait()
