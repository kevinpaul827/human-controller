"""calibration_bridge.py

Qt bridge for the Calibration module of the app which will
communicate to the frontend.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot

from .bridge_common import CameraBridgeBase
from .bridge_types import CalibrateStatusPayload, CalibrationUpdatePayload

if TYPE_CHECKING:
    from ..core.camera_manager import CameraManager


class CalibrateState(str, Enum):
    """States of calibration camera."""
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

    def __init__(self, camera_manager, gesture_store=None):
        """Initilization of calibration bridge and connect camera manager events."""
        super().__init__()
        self._init_camera_preview_bridge(camera_manager, CalibrateState.IDLE)
        self.camera: CameraManager = camera_manager
        self.gesture_store = gesture_store

        self.camera.cameraStarted.connect(self.handle_camera_started)
        self.camera.cameraStopped.connect(self.handle_camera_stopped)
        self.camera.errorOccurred.connect(self.handle_camera_error)
        self.camera.frameProcessed.connect(self.handle_frame_processed)
        self.camera.calibrationUpdated.connect(self.handle_calibration_updated)
        self.camera.previewAspectRatioChanged.connect(self.handle_preview_aspect_ratio_changed)

    @Slot()
    def startCalibrate(self):
        """Request camera ownership for calibration bridge."""
        self.camera.start(self.BRIDGE)

    @Slot()
    def stopCalibrate(self):
        """Stops camera session owned by calibration bridge."""
        self.camera.stop(self.BRIDGE)

    @Slot(result=str)
    def getCalibrateState(self):
        """Return current calibration state."""
        return self.state.value

    @Slot(float, float, float, float, float)
    def updatePreviewBounds(self, left, top, width, height, device_pixel_ratio):
        """Update preview bounds of camera."""
        self.update_preview_bounds(left, top, width, height)

    @Slot()
    def openCameraSettings(self):
        """Open camera settings interface."""
        self.camera.openCameraSettings()

    @Slot()
    def startCalibration(self):
        """Tell the camera manager to begin calibration mode."""
        self.camera.start_calibration()

    @Slot(float, result="QVariantMap")
    def startRep(self, recording_seconds):
        """Start recording a rep for calibration."""
        try:
            self.camera.start_rep(recording_seconds)
            return {"ok": True}
        except ValueError as error:
            return {"error": str(error)}

    @Slot(result="QVariantMap")
    def stopRep(self):
        """Stop current rep recording and return saved rep."""
        try:
            return self.camera.stop_rep()
        except ValueError as error:
            return {"error": str(error)}

    @Slot()
    def cancelRep(self):
        """Cancel current rep recording."""
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
        """Return all saved gestures."""
        if self.gesture_store is not None:
            return self.gesture_store.list_gestures()
        return self.camera.list_saved_gestures()

    @Slot(result="QVariantList")
    def getLoadedSessionGestures(self):
        """Return gestures loaded in current session."""
        return self.camera.loaded_session_gestures()

    @Slot(str, result="QVariantMap")
    def loadSavedGesture(self, gesture_id):
        """Load a saved gesture."""
        try:
            return self.camera.load_saved_gesture(gesture_id)
        except ValueError as error:
            return {"error": str(error)}
        except FileNotFoundError:
            return {"error": "Selected gesture could not be found."}

    def handle_calibration_updated(self, payload: CalibrationUpdatePayload):
        """Forward calibration progress payload."""
        if not self.check_camera_ownership():
            return

        self.calibrationUpdated.emit(payload)

    def _emit_status_payload(self, payload: CalibrateStatusPayload) -> None:
        """Forward calibration status payload."""
        self.calibrateStatusChanged.emit(payload)
