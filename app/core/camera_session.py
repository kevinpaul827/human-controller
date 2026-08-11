"""camera_session.py

Manages camera permissions, lifecycle of device,
and video frame delivery."
"""

import sys

from PySide6.QtCore import (
    QCameraPermission,
    QCoreApplication,
    QElapsedTimer,
    QObject,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import (
    QCamera,
    QMediaCaptureSession,
    QMediaDevices,
    QVideoFrame,
    QVideoSink,
)

from ..utils.logging_utils import log_debug, log_info


class CameraSession(QObject):
    cameraStarted = Signal(str)
    cameraStopped = Signal(str)
    errorOccurred = Signal(str, str)
    frameReady = Signal(QImage, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_bridge = None
        self.active_camera = None
        self.capture_session = None
        self.video_sink = QVideoSink(self)
        self.camera_timer = QElapsedTimer()
        self._active = False
        self._stopping = False
        self.video_sink.videoFrameChanged.connect(self.handle_video_frame)

    @property
    def active(self) -> bool:
        return self._active

    def start(self, bridge) -> None:
        if self._active and self.active_bridge == bridge:
            return
        if self.active_bridge is not None and self.active_bridge != bridge:
            self.stop()

        self.active_bridge = bridge
        if self.check_camera_permissions() and self.create_camera():
            self.start_camera()

    def stop(self) -> None:
        stopping_bridge = self._deactivate()
        if stopping_bridge is not None:
            self.cameraStopped.emit(stopping_bridge)

    def permission_denied_message(self) -> str:
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

    def check_camera_permissions(self) -> bool:
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

    def create_camera(self) -> bool:
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

    def start_camera(self) -> None:
        if self.active_bridge is None:
            return
        if self.active_camera is None and not self.create_camera():
            return
        self.camera_timer.restart()
        log_info("[camera_session] starting camera session")
        self.active_camera.start()

    def release_camera(self) -> None:
        if self.active_camera is not None:
            self.active_camera.stop()
            self.active_camera.deleteLater()
            self.active_camera = None
        if self.capture_session is not None:
            self.capture_session.setCamera(None)
            self.capture_session.setVideoSink(None)
            self.capture_session.deleteLater()
            self.capture_session = None

    def emit_camera_error(self, message: str) -> None:
        if self.active_bridge is None:
            return
        stopping_bridge = self._deactivate()
        if stopping_bridge is not None:
            self.errorOccurred.emit(message, stopping_bridge)

    @Slot(QCameraPermission)
    def handle_request_camera(self, permission) -> None:
        app = QCoreApplication.instance()
        if app.checkPermission(permission) == Qt.PermissionStatus.Granted:
            if self.active_bridge is not None and self.create_camera():
                self.start_camera()
            return
        self.emit_camera_error(self.permission_denied_message())

    @Slot(bool)
    def handle_active_changed(self, active: bool) -> None:
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

    @Slot(object, str)
    def handle_error_occurred(self, _error, error_message: str) -> None:
        if sys.platform == "win32":
            message = (
                error_message
                or "Windows blocked camera access. Check Privacy & security > Camera."
            )
        else:
            message = error_message or "Unable to start camera session."
        self.emit_camera_error(message)

    @Slot(QVideoFrame)
    def handle_video_frame(self, video_frame: QVideoFrame) -> None:
        if not self._active or self.active_bridge is None:
            return
        image = video_frame.toImage()
        if image.isNull():
            log_debug("[camera_session] skipped null video frame")
            return
        timestamp_ms = video_frame.startTime() // 1000
        if timestamp_ms < 0:
            timestamp_ms = self.camera_timer.elapsed()
        self.frameReady.emit(image.copy(), int(timestamp_ms))

    def _deactivate(self):
        self._stopping = True
        self._active = False
        self.release_camera()
        stopping_bridge = self.active_bridge
        self.active_bridge = None
        self._stopping = False
        return stopping_bridge
