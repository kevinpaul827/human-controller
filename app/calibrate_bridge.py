from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot

from .camera_manager import CameraManager

class CalibrateState(str, Enum):
    IDLE = "idle"
    LIVE = "live"
    ERROR = "error"


class CalibrateBridge(QObject):
    BRIDGE = "calibrate"

    calibrateStatusChanged = Signal(dict)
    calibrationUpdated = Signal(dict)
    previewBoundsChanged = Signal(int, int, int, int)
    previewAspectRatioChanged = Signal(float)
    poseEstimated = Signal(dict)

    def __init__(self, camera_manager):
        super().__init__()
        self.state = CalibrateState.IDLE
        self.preview_widget = None
        self.preview_bounds = (0, 0, 0, 0)
        self.camera: CameraManager = camera_manager

        self.camera.cameraStarted.connect(self.handle_camera_started)
        self.camera.cameraStopped.connect(self.handle_camera_stopped)
        self.camera.errorOccurred.connect(self.handle_camera_error)
        self.camera.frameProcessed.connect(self.handle_frame_processed)
        self.camera.calibrationUpdated.connect(self.handle_calibration_updated)
        self.camera.previewAspectRatioChanged.connect(self.handle_preview_aspect_ratio_changed)
    
    def check_camera_ownership(self):
        return self.camera.active_bridge == self.BRIDGE

    def attach_preview_widget(self, preview_widget):
        self.preview_widget = preview_widget
        self.preview_widget.hide()

    def set_state(self, state):
        self.state = state
        self.calibrateStatusChanged.emit({"state": self.state.value})

    def emit_error(self, message):
        self.state = CalibrateState.ERROR
        self.calibrateStatusChanged.emit({"state": self.state.value, "message": message})
        self.clear_preview()

    def apply_preview_bounds(self):
        if self.preview_widget is None:
            return

        left, top, width, height = self.preview_bounds
        self.previewBoundsChanged.emit(left, top, width, height)

        if self.state == CalibrateState.LIVE and width > 0 and height > 0 and self.check_camera_ownership():
            self.preview_widget.show()
            self.preview_widget.raise_()
        else:
            self.preview_widget.hide()
    
    def clear_preview(self):
        if self.preview_widget is not None:
            self.preview_widget.hide()
            self.preview_widget.clear_pose()
            self.preview_widget.clear_frame() 

    def handle_camera_started(self, bridge):
        if bridge != self.BRIDGE:
            return

        self.set_state(CalibrateState.LIVE)
        self.apply_preview_bounds()
    
    def handle_camera_stopped(self, bridge):
        if bridge != self.BRIDGE:
            return

        self.set_state(CalibrateState.IDLE)
        self.clear_preview()

    def handle_camera_error(self, message, bridge):
        if bridge != self.BRIDGE:
            return

        self.emit_error(message)

    def handle_frame_processed(self, frame, pose):
        if not self.check_camera_ownership():
            return

        if self.state != CalibrateState.LIVE:
            return
        
        if self.preview_widget is not None:
            self.preview_widget.set_frame(frame)
        
        self.poseEstimated.emit(pose)
    
    def handle_preview_aspect_ratio_changed(self, aspect_ratio):
        if not self.check_camera_ownership():
            return
        
        self.previewAspectRatioChanged.emit(aspect_ratio)

    def handle_calibration_updated(self, payload):
        if not self.check_camera_ownership():
            return

        self.calibrationUpdated.emit(payload)

    @Slot()
    def startCalibrate(self):
        self.camera.start(self.BRIDGE)

    @Slot()
    def stopCalibrate(self):
        self.camera.stop(self.BRIDGE)

    @Slot(result=str)
    def getCalibrateState(self):
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
    def startCalibration(self):
        """Tell the camera manager to begin calibration mode."""
        self.camera.start_calibration()

    @Slot(result="QVariantMap")
    def captureRep(self):
        """Ask the camera manager to save the current held pose as one rep."""
        try:
            return self.camera.capture_rep()
        except ValueError as error:
            return {"error": str(error)}

    @Slot()
    def resetRep(self):
        """Clear the current calibration data so the user can start over."""
        self.camera.reset_rep()

    @Slot(str, result="QVariantMap")
    def saveRep(self, name):
        """Save the captured reps as a new gesture template with the given name."""
        try:
            return self.camera.save_rep(name)
        except ValueError as error:
            return {"error": str(error)}

    @Slot(result="QVariantList")
    def listSavedGestures(self):
        # FIXME: this should comes from self.gesture_store.list_saved_gestures()
        return self.camera.list_saved_gestures()

    @Slot(result="QVariantList")
    def getLoadedSessionGestures(self):
        return self.camera.loaded_session_gestures()

    @Slot(str, result="QVariantMap")
    def loadSavedGesture(self, gesture_id):
        try:
            return self.camera.load_saved_gesture(gesture_id)
        except ValueError as error:
            return {"error": str(error)}
        except FileNotFoundError:
            return {"error": "Selected gesture could not be found."}
