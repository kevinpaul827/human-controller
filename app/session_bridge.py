from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot

from .camera_manager import CameraManager

class SessionState(str, Enum):
    IDLE = "idle"
    LIVE = "live"
    ERROR = "error"


class SessionBridge(QObject):
    sessionStatusChanged = Signal(dict)
    previewBoundsChanged = Signal(int, int, int, int)
    previewAspectRatioChanged = Signal(float)
    poseEstimated = Signal(dict)

    def __init__(self, camera_manager):
        super().__init__()
        self.state = SessionState.IDLE
        self.preview_widget = None
        self.preview_bounds = (0, 0, 0, 0)
        self.camera: CameraManager = camera_manager

        self.camera.cameraStarted.connect(self.handle_camera_started)
        self.camera.cameraStopped.connect(self.handle_camera_stopped)
        self.camera.errorOccurred.connect(self.handle_camera_error)
        self.camera.frameProcessed.connect(self.handle_frame_processed)
        self.camera.previewAspectRatioChanged.connect(self.previewAspectRatioChanged)

    def attach_preview_widget(self, preview_widget):
        self.preview_widget = preview_widget
        self.preview_widget.hide()

    def set_state(self, state):
        self.state = state
        self.sessionStatusChanged.emit({"state": self.state.value})

    def emit_error(self, message):
        self.camera.stop_camera()
        self.state = SessionState.ERROR
        self.sessionStatusChanged.emit({"state": self.state.value, "message": message})

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

    def handle_camera_started(self):
        self.set_state(SessionState.LIVE)
        self.apply_preview_bounds()
    
    def handle_camera_stopped(self):
        self.set_state(SessionState.IDLE)

    def handle_camera_error(self, message):
        self.emit_error(message)

    def handle_frame_processed(self, frame, pose):
        if self.state != SessionState.LIVE:
            return
        
        if self.preview_widget is not None:
            self.preview_widget.set_frame(frame)
        
        self.poseEstimated.emit(pose)

    @Slot()
    def startSession(self):
        if self.camera.active_camera is not None:
            self.set_state(SessionState.LIVE)
            self.apply_preview_bounds()
            return

        self.camera.start()

    @Slot()
    def stopSession(self):
        self.camera.stop_camera()

        if self.preview_widget is not None:
            self.preview_widget.hide()

    @Slot(result=str)
    def getSessionState(self):
        return self.state.value

    @Slot(float, float, float, float, float)
    def updatePreviewBounds(self, left, top, width, height, device_pixel_ratio):
        self.preview_bounds = (
            max(0, round(left)),
            max(0, round(top)),
            max(0, round(width)),
            max(0, round(height)),
        )
        self.apply_preview_bounds()

    @Slot()
    def openCameraSettings(self):
        self.camera.openCameraSettings()
