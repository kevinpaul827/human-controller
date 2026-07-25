from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot

from .camera_manager import CameraManager

class SessionState(str, Enum):
    IDLE = "idle"
    LIVE = "live"
    ERROR = "error"


class SessionBridge(QObject):
    BRIDGE = "session"

    sessionStatusChanged = Signal(dict)
    previewBoundsChanged = Signal(int, int, int, int)
    previewAspectRatioChanged = Signal(float)
    poseEstimated = Signal(dict)
    gestureMatchUpdated = Signal(dict)
    overlayVisibilityChanged = Signal(bool)

    def __init__(self, camera_manager):
        super().__init__()
        self.state = SessionState.IDLE
        self.preview_widget = None
        self.preview_bounds = (0, 0, 0, 0)
        self.picture_in_picture = None
        self.overlay_requested = True
        self.camera: CameraManager = camera_manager

        self.camera.cameraStarted.connect(self.handle_camera_started)
        self.camera.cameraStopped.connect(self.handle_camera_stopped)
        self.camera.errorOccurred.connect(self.handle_camera_error)
        self.camera.frameProcessed.connect(self.handle_frame_processed)
        self.camera.previewFrameReady.connect(self.handle_preview_frame)
        self.camera.gestureMatchUpdated.connect(self.handle_gesture_match_updated)
        self.camera.previewAspectRatioChanged.connect(self.handle_preview_aspect_ratio_changed)

    def check_camera_ownership(self):
        return self.camera.active_bridge == self.BRIDGE

    def attach_preview_widget(self, preview_widget):
        self.preview_widget = preview_widget
        self.preview_widget.hide()

    def attach_picture_in_picture(self, window):
        self.picture_in_picture = window
        self.picture_in_picture.visibilityChanged.connect(
            self.handle_overlay_visibility_changed
        )

    def handle_overlay_visibility_changed(self, visible):
        self.overlay_requested = bool(visible)
        self.overlayVisibilityChanged.emit(bool(visible))

    def apply_overlay_visibility(self):
        if self.picture_in_picture is None:
            return

        should_show = (
            self.overlay_requested
            and self.state == SessionState.LIVE
            and self.check_camera_ownership()
        )
        if should_show:
            self.picture_in_picture.show_overlay()
        else:
            self.picture_in_picture.hide_overlay()

    def set_state(self, state):
        self.state = state
        self.sessionStatusChanged.emit({"state": self.state.value})

    def emit_error(self, message):
        self.state = SessionState.ERROR
        self.sessionStatusChanged.emit({"state": self.state.value, "message": message})
        self.clear_preview()
        self.apply_overlay_visibility()

    def apply_preview_bounds(self):
        if self.preview_widget is None:
            return

        left, top, width, height = self.preview_bounds
        self.previewBoundsChanged.emit(left, top, width, height)

        if self.state == SessionState.LIVE and width > 0 and height > 0 and self.check_camera_ownership():
            self.preview_widget.show()
            self.preview_widget.raise_()
        else:
            self.preview_widget.hide()

    def clear_preview(self):
        if self.preview_widget is not None:
            self.preview_widget.hide()
            self.preview_widget.clear_pose()
            self.preview_widget.clear_frame()
        if self.picture_in_picture is not None:
            self.picture_in_picture.clear()

    def handle_camera_started(self, bridge):
        if bridge != self.BRIDGE:
            return

        self.set_state(SessionState.LIVE)
        self.apply_preview_bounds()
        self.apply_overlay_visibility()

    def handle_camera_stopped(self, bridge):
        if bridge != self.BRIDGE:
            return

        self.set_state(SessionState.IDLE)
        self.clear_preview()
        self.apply_overlay_visibility()

    def handle_camera_error(self, message, bridge):
        if bridge != self.BRIDGE:
            return

        self.emit_error(message)

    def handle_frame_processed(self, frame, pose):
        if not self.check_camera_ownership():
            return

        if self.state != SessionState.LIVE:
            return

        if self.picture_in_picture is not None:
            self.picture_in_picture.set_pose(pose)



        self.poseEstimated.emit(pose)

    def handle_preview_frame(self, frame):
        if not self.check_camera_ownership() or self.state != SessionState.LIVE:
            return
        if self.picture_in_picture is not None:
            self.picture_in_picture.set_frame(frame)

    def handle_preview_aspect_ratio_changed(self, aspect_ratio):
        if not self.check_camera_ownership():
            return

        self.previewAspectRatioChanged.emit(aspect_ratio)

    def handle_gesture_match_updated(self, payload):
        if not self.check_camera_ownership():
            return

        if self.state != SessionState.LIVE:
            return

        if self.picture_in_picture is not None:
            self.picture_in_picture.show_match(payload)
        self.gestureMatchUpdated.emit(payload)

    @Slot()
    def startSession(self):
        self.overlay_requested = True
        self.camera.start(self.BRIDGE)

    @Slot()
    def stopSession(self):
        self.camera.stop(self.BRIDGE)

    @Slot(bool)
    def setOverlayVisible(self, visible):
        self.overlay_requested = bool(visible)
        self.apply_overlay_visibility()

    @Slot(result=bool)
    def getOverlayVisible(self):
        return bool(
            self.picture_in_picture is not None
            and self.picture_in_picture.isVisible()
        )

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

    @Slot()
    def openAccessibilitySettings(self):
        self.camera.openAccessibilitySettings()
