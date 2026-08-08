from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot

from ..profile_manager import ProfileError, ProfileManager
from .bridge_common import CameraBridgeBase
from .bridge_types import GestureMatchPayload, PosePayload, SessionStatusPayload

if TYPE_CHECKING:
    from ..core.camera_manager import CameraManager
    from .state_bridge import StateBridge


class SessionState(str, Enum):
    IDLE = "idle"
    LIVE = "live"
    ERROR = "error"


class SessionBridge(CameraBridgeBase, QObject):
    BRIDGE = "session"
    IDLE_STATE = SessionState.IDLE
    LIVE_STATE = SessionState.LIVE
    ERROR_STATE = SessionState.ERROR

    sessionStatusChanged = Signal(dict)
    previewBoundsChanged = Signal(int, int, int, int)
    previewAspectRatioChanged = Signal(float)
    poseEstimated = Signal(dict)
    gestureMatchUpdated = Signal(dict)

    def __init__(
        self,
        camera_manager: CameraManager,
        profile_manager: ProfileManager | StateBridge | None = None,
    ):
        super().__init__()
        self._init_camera_preview_bridge(camera_manager, SessionState.IDLE)
        self.picture_in_picture = None
        self.state_bridge = (
            profile_manager
            if hasattr(profile_manager, "runtime_configuration")
            else None
        )
        self.profile_manager = (
            self.state_bridge.profile_manager
            if self.state_bridge is not None
            else profile_manager
        )
        self.active_patient_id = None
        self.active_key_bindings = {}

        self.camera.cameraStarted.connect(self.handle_camera_started)
        self.camera.cameraStopped.connect(self.handle_camera_stopped)
        self.camera.errorOccurred.connect(self.handle_camera_error)
        preview_frame_ready = getattr(self.camera, "previewFrameReady", None)
        if preview_frame_ready is not None:
            preview_frame_ready.connect(self.handle_preview_frame)
        self.camera.frameProcessed.connect(self.handle_frame_processed)
        self.camera.gestureMatchUpdated.connect(self.handle_gesture_match_updated)
        self.camera.previewAspectRatioChanged.connect(self.handle_preview_aspect_ratio_changed)

    def attach_picture_in_picture(self, window):
        self.picture_in_picture = window

    @Slot(str, result="QVariantMap")
    def loadProfile(self, patient_id):
        return self._profile_result(patient_id)

    @Slot()
    def startSession(self):
        self.camera.start(self.BRIDGE)

    @Slot()
    def stopSession(self):
        self.camera.stop(self.BRIDGE)
        if self.state_bridge is None:
            self._clear_profile()
        if self.state != SessionState.IDLE:
            self.set_state(SessionState.IDLE)
            self.clear_preview()
            self.apply_overlay_visibility()

    @Slot(result=str)
    def getSessionState(self):
        return self.state.value
    
    @Slot(result="QVariantList")
    def getLoadedSessionGestures(self):
        if hasattr(self.camera, "session_gesture_mappings"):
            return self.camera.session_gesture_mappings()
        if self.state_bridge is None:
            return []
        runtime = self.state_bridge.runtime_configuration()
        snapshot = self.state_bridge.getState()
        gestures_by_id = {
            item["gestureId"]: item
            for item in snapshot.get("gestures", [])
            if item.get("calibratedAt")
        }
        return [
            {
                "gestureId": gesture_id,
                "name": gestures_by_id[gesture_id]["name"],
                "key": key,
            }
            for gesture_id, key in runtime["bindings"].items()
            if gesture_id in gestures_by_id
        ]

    @Slot(float, float, float, float, float)
    def updatePreviewBounds(self, left, top, width, height, device_pixel_ratio):
        self.update_preview_bounds(left, top, width, height)

    @Slot()
    def openCameraSettings(self):
        self.camera.openCameraSettings()

    @Slot()
    def openAccessibilitySettings(self):
        self.camera.openAccessibilitySettings()

    def handle_preview_frame(self, frame, timestamp_ms):
        if not self.check_camera_ownership() or self.state != SessionState.LIVE:
            return
        if self.picture_in_picture is not None:
            self.picture_in_picture.set_frame(frame, timestamp_ms)

    def handle_gesture_match_updated(self, payload: GestureMatchPayload):
        if not self.check_camera_ownership():
            return

        if self.state != SessionState.LIVE:
            return

        enriched_payload: GestureMatchPayload = dict(payload)
        gesture_id = enriched_payload.get("gestureId")
        if not enriched_payload.get("key"):
            enriched_payload["key"] = self.active_key_bindings.get(gesture_id)
        if self.picture_in_picture is not None:
            self.picture_in_picture.show_match(enriched_payload)
        self.gestureMatchUpdated.emit(enriched_payload)

    def apply_overlay_visibility(self):
        if self.picture_in_picture is None:
            return

        should_show = (
            self.state == SessionState.LIVE
            and self.check_camera_ownership()
        )
        if should_show:
            self.picture_in_picture.show_overlay()
        else:
            self.picture_in_picture.hide_overlay()

    def _emit_status_payload(self, payload: SessionStatusPayload) -> None:
        self.sessionStatusChanged.emit(payload)

    def _after_state_change(self) -> None:
        self.apply_overlay_visibility()

    def _clear_extra_preview(self) -> None:
        if self.picture_in_picture is not None:
            self.picture_in_picture.clear()

    def _handle_live_pose(self, pose: PosePayload) -> None:
        if self.picture_in_picture is not None:
            self.picture_in_picture.set_pose(pose)

    def _load_profile(self, patient_id):
        if self.profile_manager is None:
            raise ProfileError("Profile state is unavailable.")
        snapshot = (
            self.state_bridge.selectPatient(str(patient_id))
            if self.state_bridge is not None
            else None
        )
        profile = self.profile_manager.load(patient_id)
        self.active_patient_id = profile.patient_id
        self.active_key_bindings = dict(profile.key_bindings)
        if hasattr(self.camera, "configure_session_gestures"):
            gestures = self.camera.configure_session_gestures(
                self.active_key_bindings
            )
        elif snapshot is not None:
            gestures_by_id = {
                item["gestureId"]: item
                for item in snapshot.get("gestures", [])
                if item.get("calibratedAt")
            }
            gestures = [
                {
                    "gestureId": gesture_id,
                    "name": gestures_by_id[gesture_id]["name"],
                    "key": key,
                }
                for gesture_id, key in self.active_key_bindings.items()
                if gesture_id in gestures_by_id
            ]
        else:
            gestures = []
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
        if (
            self.state_bridge is None
            and hasattr(self.camera, "clear_session_gestures")
        ):
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
