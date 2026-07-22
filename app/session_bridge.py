from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot

from .camera_manager import CameraManager
from .profile_manager import ProfileError, ProfileManager

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

    def __init__(
        self,
        camera_manager: CameraManager,
        profile_manager: ProfileManager,
    ):
        super().__init__()
        self.state = SessionState.IDLE
        self.preview_widget = None
        self.preview_bounds = (0, 0, 0, 0)
        self.camera = camera_manager
        self.profile_manager = profile_manager
        self.active_patient_id = None
        self.active_key_bindings = {}

        self.camera.cameraStarted.connect(self.handle_camera_started)
        self.camera.cameraStopped.connect(self.handle_camera_stopped)
        self.camera.errorOccurred.connect(self.handle_camera_error)
        self.camera.frameProcessed.connect(self.handle_frame_processed)
        self.camera.gestureMatchUpdated.connect(self.handle_gesture_match_updated)
        self.camera.previewAspectRatioChanged.connect(self.handle_preview_aspect_ratio_changed)
    
    def check_camera_ownership(self):
        return self.camera.active_bridge == self.BRIDGE

    def attach_preview_widget(self, preview_widget):
        self.preview_widget = preview_widget
        self.preview_widget.hide()

    def set_state(self, state):
        self.state = state
        self.sessionStatusChanged.emit({"state": self.state.value})

    def emit_error(self, message):
        self.state = SessionState.ERROR
        self.sessionStatusChanged.emit({"state": self.state.value, "message": message})
        self.clear_preview()

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

    def handle_camera_started(self, bridge):
        if bridge != self.BRIDGE:
            return

        self.set_state(SessionState.LIVE)
        self.apply_preview_bounds()
    
    def handle_camera_stopped(self, bridge):
        if bridge != self.BRIDGE:
            return

        self.set_state(SessionState.IDLE)
        self.clear_preview()

    def handle_camera_error(self, message, bridge):
        if bridge != self.BRIDGE:
            return

        self.emit_error(message)

    def handle_frame_processed(self, frame, pose):
        if not self.check_camera_ownership():
            return

        if self.state != SessionState.LIVE:
            return
        
        if self.preview_widget is not None:
            self.preview_widget.set_frame(frame)
        
        self.poseEstimated.emit(pose)
    
    def handle_preview_aspect_ratio_changed(self, aspect_ratio):
        if not self.check_camera_ownership():
            return
        
        self.previewAspectRatioChanged.emit(aspect_ratio)

    def handle_gesture_match_updated(self, payload):
        if not self.check_camera_ownership():
            return

        if self.state != SessionState.LIVE:
            return

        enriched_payload = dict(payload)
        gesture_id = enriched_payload.get("gestureId")
        enriched_payload["key"] = self.active_key_bindings.get(gesture_id)
        self.gestureMatchUpdated.emit(enriched_payload)

    def _load_profile(self, patient_id):
        profile = self.profile_manager.load(patient_id)
        self.active_patient_id = profile.patient_id
        self.active_key_bindings = dict(profile.key_bindings)
        gestures = self.camera.configure_session_gestures(
            self.active_key_bindings
        )
        loaded_ids = {gesture["gestureId"] for gesture in gestures}
        return {
            "patientId": profile.patient_id,
            "gestures": gestures,
            "missingGestureIds": [
                gesture_id
                for gesture_id in self.active_key_bindings
                if gesture_id not in loaded_ids
            ],
        }

    def _clear_profile(self):
        self.camera.clear_session_gestures()
        self.active_patient_id = None
        self.active_key_bindings = {}

    def _profile_result(self, patient_id):
        try:
            return {"ok": True, "data": self._load_profile(patient_id)}
        except (OSError, ProfileError, ValueError) as error:
            self._clear_profile()
            self.emit_error(str(error))
            return {"ok": False, "error": str(error)}

    @Slot(str, result="QVariantMap")
    def loadProfile(self, patient_id):
        return self._profile_result(patient_id)

    @Slot()
    def startSession(self):
        # Keep the original no-arg contract used by existing session UI.
        self.camera.start(self.BRIDGE)

    @Slot()
    def stopSession(self):
        self.camera.stop(self.BRIDGE)
        self._clear_profile()
        if self.state != SessionState.IDLE:
            self.set_state(SessionState.IDLE)

    @Slot(result=str)
    def getSessionState(self):
        return self.state.value
    
    @Slot(result="QVariantList")
    def getLoadedSessionGestures(self):
        return self.camera.session_gesture_mappings()

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
