import sys
from enum import Enum

from PySide6.QtCore import QCameraPermission, QCoreApplication, QElapsedTimer, QObject, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices, QVideoFrame
from PySide6.QtMultimediaWidgets import QVideoWidget

from .pose_processor import PoseProcessor

class SessionState(str, Enum):
    IDLE = "idle"
    LIVE = "live"
    ERROR = "error"


class SessionBridge(QObject):
    sessionStatusChanged = Signal(dict)
    previewBoundsChanged = Signal(int, int, int, int)

    processFrame = Signal(object, int)
    poseEstimated = Signal(dict)
    closePoseProcessor = Signal()

    def __init__(self):
        super().__init__()
        self.state = SessionState.IDLE
        self.active_camera = None
        self.camera_timer = QElapsedTimer()
        self.capture_session = None
        self.preview_widget = None
        self.preview_bounds = (0, 0, 0, 0)
        self.video_sink = None

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
        self.pose_thread.start()

    def attach_preview_widget(self, preview_widget: QVideoWidget):
        self.preview_widget = preview_widget
        self.preview_widget.hide()

        self.video_sink = self.preview_widget.videoSink()
        self.video_sink.videoFrameChanged.connect(self.handle_video_frame)

        if self.capture_session is not None:
            self.capture_session.setVideoOutput(self.preview_widget)

    def set_state(self, state):
        self.state = state
        self.sessionStatusChanged.emit({"state": self.state.value})

    def emit_error(self, message):
        self.stop_camera()
        self.state = SessionState.ERROR
        self.sessionStatusChanged.emit({"state": self.state.value, "message": message})

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
            self.emit_error(self.permission_denied_message())
            return False

        app.requestPermission(permission, self, self.handle_request_camera)
        return False

    def ensure_camera_session(self):
        if self.active_camera is not None and self.capture_session is not None:
            return True

        video_input = QMediaDevices.defaultVideoInput()

        if video_input.isNull():
            self.emit_error("No camera detected on this device.")
            return False

        self.stop_camera()

        self.active_camera = QCamera(video_input)
        self.capture_session = QMediaCaptureSession()
        self.capture_session.setCamera(self.active_camera)

        if self.preview_widget is not None:
            self.capture_session.setVideoOutput(self.preview_widget)

        self.active_camera.activeChanged.connect(self.handle_active_changed)
        self.active_camera.errorOccurred.connect(self.handle_error_occurred)
        return True

    def start_camera(self):
        if not self.ensure_camera_session():
            return

        self.camera_timer.restart()
        self.active_camera.start()
        self.set_state(SessionState.LIVE)
        self.apply_preview_bounds()

    def stop_camera(self):
        if self.preview_widget is not None:
            self.preview_widget.hide()

        if self.active_camera is not None:
            self.active_camera.stop()
            self.active_camera.deleteLater()
            self.active_camera = None

        if self.capture_session is not None:
            self.capture_session.setCamera(None)
            self.capture_session.setVideoOutput(None)
            self.capture_session.deleteLater()
            self.capture_session = None

    def apply_preview_bounds(self):
        if self.preview_widget is None:
            return

        left, top, width, height = self.preview_bounds
        self.previewBoundsChanged.emit(left, top, width, height)

        if self.state == SessionState.LIVE and width > 0 and height > 0:
            self.preview_widget.show()
            self.preview_widget.raise_()
        else:
            self.preview_widget.hide()

    def handle_request_camera(self, permission):
        app = QCoreApplication.instance()

        if app.checkPermission(permission) == Qt.PermissionStatus.Granted:
            self.start_camera()
        else:
            self.emit_error(self.permission_denied_message())

    def handle_active_changed(self, active):
        if active and self.state != SessionState.LIVE:
            self.set_state(SessionState.LIVE)
            self.apply_preview_bounds()

    def handle_error_occurred(self, error, error_message):
        if sys.platform == "win32":
            message = (
                error_message
                or "Windows blocked camera access. Check Privacy & security > Camera."
            )
        else:
            message = error_message or "Unable to start camera session."

        self.emit_error(message)
    
    def handle_video_frame(self, video_frame: QVideoFrame):
        if self.state != SessionState.LIVE:
            return

        if self.pose_processing:
            return
        
        image = video_frame.toImage()

        if image.isNull():
            return
        
        timestamp_ms = video_frame.startTime() // 1000

        if timestamp_ms < 0:
            timestamp_ms = self.camera_timer.elapsed()

        self.pose_processing = True

        self.processFrame.emit(image.copy(), int(timestamp_ms))
    
    def handle_pose_estimated(self, pose):
        if self.state == SessionState.LIVE:
            if pose is None:
                self.poseEstimated.emit({
                    "detected": False,
                    "landmarks": [],
                    "visibility": []
                })
            else:
                self.poseEstimated.emit({
                    "detected": True,
                    "landmarks": pose.xyz,
                    "visibility": pose.visibility
                })
                print(pose.xyz)

    def handle_processing_finished(self):
        self.pose_processing = False
    
    def handle_pose_error(self, message):
        self.emit_error(message)

    @Slot()
    def startSession(self):
        if self.active_camera is not None:
            self.set_state(SessionState.LIVE)
            self.apply_preview_bounds()
            return

        if self.check_camera_permissions():
            self.start_camera()

    @Slot()
    def stopSession(self):
        self.stop_camera()
        self.set_state(SessionState.IDLE)

    @Slot(result=str)
    def getSessionState(self):
        return self.state.value

    @Slot(float, float, float, float, float)
    def updatePreviewBounds(self, left, top, width, height, device_pixel_ratio):
        del device_pixel_ratio

        self.preview_bounds = (
            max(0, round(left)),
            max(0, round(top)),
            max(0, round(width)),
            max(0, round(height)),
        )
        self.apply_preview_bounds()

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

        self.emit_error("Open your system camera privacy settings to allow access.")

    @Slot()
    def shutdown(self):
        self.stop_camera()

        if self.pose_thread.isRunning():
            self.closePoseProcessor.emit()
            self.pose_thread.quit()
            self.pose_thread.wait()
