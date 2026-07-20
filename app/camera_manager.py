import sys

from PySide6.QtCore import QCameraPermission, QCoreApplication, QElapsedTimer, QObject, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QImage
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices, QVideoFrame, QVideoSink

from backend.matching_engine import AngleKey, TemplateBuilder
from backend.matching_engine.core.angles import reduce_joints

from .gesture_matcher import GestureMatcher
from .gesture_store import SavedGesture
from .logging_utils import log_debug, log_info, log_verbose
from .pose_processor import PoseProcessor

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

    frameProcessed = Signal(QImage, dict)
    gestureMatchUpdated = Signal(dict)
    calibrationUpdated = Signal(dict)
    previewAspectRatioChanged = Signal(float)
    processFrame = Signal(object, int)
    closePoseProcessor = Signal()

    def __init__(self):
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
        self._preview_aspect_ratio = 4 / 3

        self.gesture_matcher = GestureMatcher()
        self.template_builder = TemplateBuilder()
        self._calibration_frames = []
        self._calibration_reps = []
        self.pose_processing = False
        self.pose_thread = QThread(self)
        self.pose_processor = PoseProcessor()
        self.pose_processor.moveToThread(self.pose_thread)

        self.processFrame.connect(self.pose_processor.process_frame, Qt.ConnectionType.QueuedConnection)
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

        self.gesture_matcher.reload_templates()
        self.camera_timer.restart()
        self._frame_log_emitted = False
        self._pending_pose_frame = QImage()
        log_info("[camera_manager] starting camera session")
        self.active_camera.start()

    def stop_camera(self):
        log_info("[camera_manager] stopping camera session")
        self._stopping = True
        self._active = False
        self._pending_pose_frame = QImage()

        self.release_camera()
        stopping_bridge = self.active_bridge
        self.active_bridge = None
        self._stopping = False
        
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
        
        self._stopping = True
        self._active = False
        self._pending_pose_frame = QImage()

        self.release_camera()
        stopping_bridge = self.active_bridge
        self.active_bridge = None
        self._stopping = False
        
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

        if self.pose_processing:
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

        if not self._frame_log_emitted:
            log_debug(
                f"[camera_manager] received first frame {image.width()}x{image.height()} at {timestamp_ms}ms"
            )
            self._frame_log_emitted = True

        self._pending_pose_frame = image.copy()
        self.pose_processing = True

        self.processFrame.emit(self._pending_pose_frame.copy(), int(timestamp_ms))

    def handle_pose_estimated(self, pose):
        if not self._active or self.active_bridge is None:
            self._pending_pose_frame = QImage()
            return

        if self._pending_pose_frame.isNull():
            return

        try:
            angles = self.gesture_matcher.angles_for_pose(pose)
            # If we are in calibration mode, save the current pose angles
            # so the user can capture them later as a calibration rep.
            if self.active_bridge == "calibrate":
                self._append_calibration_frame(angles)
            match_event = self.gesture_matcher.match_pose(pose)
            self.gestureMatchUpdated.emit(match_event.to_dict())
        except Exception as error:
            log_info(f"[camera_manager] gesture matcher error: {error}")

        if pose is None:
            log_verbose("[camera_manager] pose not detected")
            payload = {
                "detected": False,
                "landmarks": [],
                "visibility": [],
            }
        else:
            log_verbose("[camera_manager] pose detected, forwarding live landmarks")
            payload = {
                "detected": True,
                "landmarks": pose.xyz,
                "visibility": pose.visibility
            }

        frame = self._pending_pose_frame
        self._pending_pose_frame = QImage()
        self.frameProcessed.emit(frame, payload)

    def handle_processing_finished(self):
        self.pose_processing = False

    def handle_pose_error(self, message):
        log_info(f"[camera_manager] pose processor error: {message}")
        self.emit_camera_error(message)

############################## Calibration Methods #############################
    def _append_calibration_frame(self, angles):
        if not angles:
            return
        self._calibration_frames.append(angles)

    def _emit_calibration_updated(self):
        self.calibrationUpdated.emit(
            {
                "repCount": len(self._calibration_reps),
                "capturing": self.active_bridge == "calibrate" and self._active,
            }
        )

    def start_calibration(self):
        """Start a new calibration session.

        This clears any old pose frames and reps, and tells the UI that
        calibration has started.
        """
        self._calibration_frames = []
        self._calibration_reps = []
        self._emit_calibration_updated()

    def capture_rep(self):
        """Capture the current held pose as one calibration rep.

        The method averages the saved pose frames for this rep and stores the
        result. It also clears the current capture frames so the next rep can be recorded.
        """
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
        self._emit_calibration_updated()

    def save_rep(self, name):
        """Save the captured reps as a new gesture template.

        The given name is required. Saved reps are converted into a gesture and
        stored for later matching.
        """
        resolved_name = str(name or "").strip()
        if not resolved_name:
            raise ValueError("Gesture name is required.")
        if not self._calibration_reps:
            raise ValueError("Capture at least one rep before saving.")

        active_joints = [
            joint
            for joint in AngleKey
            if any(rep.get(joint) is not None for rep in self._calibration_reps)
        ]
        template = self.template_builder.build(
            [[rep] for rep in self._calibration_reps],
            name=resolved_name,
            active_joints=active_joints or None,
        )
        saved = SavedGesture(
            gesture_id=template.gesture_id,
            name=template.name,
            type=template.type,
            regions=[],
            active_joints=[joint.value for joint in template.active_joints],
            target_angles={joint.value: float(value) for joint, value in template.target_angles.items()},
            tolerance_deg={joint.value: float(value) for joint, value in template.tolerance_deg.items()},
            trajectory=list(template.trajectory),
            fps=int(template.fps),
        )
        self.gesture_matcher.store.save(saved)
        self.gesture_matcher.reload_templates()
        self._calibration_frames = []
        self._calibration_reps = []
        self._emit_calibration_updated()
        return {
            "gestureId": saved.gesture_id,
            "name": saved.name,
            "repCount": 0,
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
    def shutdown(self):
        self.stop_camera()

        if self.pose_thread.isRunning():
            self.closePoseProcessor.emit()
            self.pose_thread.quit()
            self.pose_thread.wait()
