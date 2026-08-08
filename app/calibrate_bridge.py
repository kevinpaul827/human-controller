from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot

from .bridge_common import CameraBridgeBase
from .camera_manager import CameraManager


class CalibrateState(str, Enum):
    IDLE = "idle"
    LIVE = "live"
    ERROR = "error"


class CalibrateBridge(CameraBridgeBase, QObject):
    BRIDGE = "calibrate"
    IDLE_STATE = CalibrateState.IDLE
    LIVE_STATE = CalibrateState.LIVE
    ERROR_STATE = CalibrateState.ERROR

    calibrateStatusChanged = Signal(dict)
    calibrationUpdated = Signal(dict)
    previewBoundsChanged = Signal(int, int, int, int)
    previewAspectRatioChanged = Signal(float)
    poseEstimated = Signal(dict)

    def __init__(self, camera_manager):
        super().__init__()
        self._init_camera_preview_bridge(camera_manager, CalibrateState.IDLE)
        self.camera: CameraManager = camera_manager

        self.camera.cameraStarted.connect(self.handle_camera_started)
        self.camera.cameraStopped.connect(self.handle_camera_stopped)
        self.camera.errorOccurred.connect(self.handle_camera_error)
        self.camera.frameProcessed.connect(self.handle_frame_processed)
        self.camera.calibrationUpdated.connect(self.handle_calibration_updated)
        self.camera.previewAspectRatioChanged.connect(self.handle_preview_aspect_ratio_changed)

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
        self.update_preview_bounds(left, top, width, height)

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

    @Slot(float, result="QVariantMap")
    def startRep(self, recording_seconds):
        try:
            self.camera.start_rep(recording_seconds)
            return {"ok": True}
        except ValueError as error:
            return {"error": str(error)}

    @Slot(result="QVariantMap")
    def stopRep(self):
        try:
            return self.camera.stop_rep()
        except ValueError as error:
            return {"error": str(error)}

    @Slot()
    def cancelRep(self):
        self.camera.cancel_rep()

    @Slot()
    def resetRep(self):
        """Clear the current calibration data so the user can start over."""
        self.camera.reset_rep()

    @Slot(str, result="QVariantMap")
    @Slot(str, str, result="QVariantMap")
    def saveRep(self, name, gesture_id=""):
        """Save the captured reps as a gesture template with the given name."""
        try:
            return self.camera.save_rep(name, gesture_id or None)
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

    def handle_calibration_updated(self, payload):
        if not self.check_camera_ownership():
            return

        self.calibrationUpdated.emit(payload)

    def _emit_status_payload(self, payload: dict) -> None:
        self.calibrateStatusChanged.emit(payload)
