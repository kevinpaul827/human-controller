import sys

from PySide6.QtCore import QCameraPermission, QCoreApplication, QElapsedTimer, QObject, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QImage
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices, QVideoFrame, QVideoSink

from .logging_utils import log_debug, log_info, log_verbose
from .pose_processor import PoseProcessor

class CameraManager(QObject):
    cameraStarted = Signal()
    cameraStopped = Signal()
    errorOccurred = Signal(str)

    frameProcessed = Signal(QImage, dict)
    previewAspectRatioChanged = Signal(float)
    processFrame = Signal(object, int)
    closePoseProcessor = Signal()

    def __init__(self):
        super().__init__()
        self.active_camera = None
        self.camera_timer = QElapsedTimer()
        self.capture_session = None
        self.video_sink = QVideoSink(self)

        self._active = False
        self._frame_log_emitted = False
        self._pending_pose_frame = QImage()
        self._preview_aspect_ratio = 4 / 3

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
    
    def start(self):
        if self._active:
            return
        
        if self.active_camera is not None:
            self.start_camera()
            return
        
        if self.check_camera_permissions():
            if self.create_camera:
                self.start_camera()

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
            self.errorOccurred.emit(self.permission_denied_message())
            return False

        app.requestPermission(permission, self, self.handle_request_camera)
        return False

    def create_camera(self):
        if self.active_camera is not None and self.capture_session is not None:
            return True

        video_input = QMediaDevices.defaultVideoInput()

        if video_input.isNull():
            self.errorOccurred.emit("No camera detected on this device.")
            return False

        self.stop_camera()

        self.active_camera = QCamera(video_input, self)
        self.capture_session = QMediaCaptureSession()
        self.capture_session.setCamera(self.active_camera)
        self.capture_session.setVideoSink(self.video_sink)

        self.active_camera.activeChanged.connect(self.handle_active_changed)
        self.active_camera.errorOccurred.connect(self.handle_error_occurred)
        return True

    def start_camera(self):
        if self.active_camera is None:
            if not self.create_camera():
                return

        self.camera_timer.restart()
        self._frame_log_emitted = False
        self._pending_pose_frame = QImage()
        log_info("[camera_manager] starting camera session")
        self.active_camera.start()

    def stop_camera(self):
        log_info("[camera_manager] stopping camera session")
        was_active = self._active
        self._active = False
        self._pending_pose_frame = QImage()

        if self.active_camera is not None:
            self.active_camera.stop()
            self.active_camera.deleteLater()
            self.active_camera = None

        if self.capture_session is not None:
            self.capture_session.setCamera(None)
            self.capture_session.setVideoSink(None)
            self.capture_session.deleteLater()
            self.capture_session = None
        
        if was_active:
            self.cameraStopped.emit()

    def handle_request_camera(self, permission):
        app = QCoreApplication.instance()

        if app.checkPermission(permission) == Qt.PermissionStatus.Granted:
            if self.create_camera():
                self.start_camera()
        else:
            self.errorOccurred.emit(self.permission_denied_message())

    def handle_active_changed(self, active):
        if active:
            if self._active:
                return
            
            self._active = True
            self.cameraStarted.emit()
            return
        
        if not self._active:
            return
        
        self._active = False
        self.cameraStopped.emit()

    def handle_error_occurred(self, error, error_message):
        if sys.platform == "win32":
            message = (
                error_message
                or "Windows blocked camera access. Check Privacy & security > Camera."
            )
        else:
            message = error_message or "Unable to start camera session."

        self.stop_camera()
        self.errorOccurred.emit(message)

    def handle_video_frame(self, video_frame: QVideoFrame):
        if not self._active:
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
            log_debug(f"[session_bridge] preview aspect ratio updated to {aspect_ratio:.4f}")
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
        if not self._active:
            self._pending_pose_frame = QImage()
            return

        if self._pending_pose_frame.isNull():
            return

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
        self.stop_camera()
        self.errorOccurred.emit_error(message)

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

        self.errorOccurred.emit("Open your system camera privacy settings to allow access.")

    @Slot()
    def shutdown(self):
        self.stop_camera()

        if self.pose_thread.isRunning():
            self.closePoseProcessor.emit()
            self.pose_thread.quit()
            self.pose_thread.wait()
