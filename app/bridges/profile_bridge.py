"""profile_bridge.py

Expose patient profiles and gesture names to the React frontend.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError
from PySide6.QtCore import QObject, Signal, Slot

from ..gestures.gesture_store import DEFAULT_GESTURES_DIR, GestureStore
from ..profile_manager import PatientProfile, ProfileError, ProfileManager

DEFAULT_PROFILES_DIR = Path(__file__).resolve().parent.parent / "data" / "profiles"


class ProfileBridge(QObject):
    profilesChanged = Signal()

    def __init__(
        self,
        profile_manager: ProfileManager | None = None,
        gesture_store: GestureStore | None = None,
    ) -> None:
        super().__init__()
        self.profile_manager = profile_manager or ProfileManager(DEFAULT_PROFILES_DIR)
        self.gesture_store = gesture_store or GestureStore(DEFAULT_GESTURES_DIR)

    def _success(self, data) -> str:
        """Serialize scuccessful bridge reponse."""
        return json.dumps({"ok": True, "data": data})

    def _failure(self, error: Exception) -> str:
        """Serialize unsuccessful bridge reponse."""
        return json.dumps({"ok": False, "error": str(error)})

    def _profile_data(self, profile: PatientProfile) -> dict:
        """Convert profile model into dictionary for frontend."""
        return profile.model_dump(mode="json", by_alias=True)

    @Slot(result=str)
    def listProfiles(self) -> str:
        """Return all saved patient profiles."""
        try:
            profiles = [
                self._profile_data(profile)
                for profile in self.profile_manager.list_profiles()
            ]
            return self._success(profiles)
        except (OSError, ProfileError) as error:
            return self._failure(error)

    @Slot(result=str)
    def listGestures(self) -> str:
        """Return gestureId and names of all gestures."""
        try:
            gestures = [
                {
                    "gestureId": gesture.gesture_id,
                    "name": gesture.name,
                }
                for gesture in self.gesture_store.load_all()
            ]
            return self._success(gestures)
        except OSError as error:
            return self._failure(error)

    @Slot(str, str, result=str)
    def createProfile(
        self,
        patient_name: str,
        notes: str,
    ) -> str:
        """Create and save a new profile."""
        try:
            created = self.profile_manager.create_new(
                patient_name.strip(),
                notes.strip(),
            )
            self.profilesChanged.emit()
            return self._success(self._profile_data(created))
        except (OSError, ProfileError, ValidationError) as error:
            return self._failure(error)

    @Slot(str, result=str)
    def deleteProfile(self, patient_id: str) -> str:
        """Delete a profile and save changes."""
        try:
            self.profile_manager.delete(patient_id)
            self.profilesChanged.emit()
            return self._success(patient_id)
        except (OSError, ProfileError) as error:
            return self._failure(error)

    @Slot(str, str, str, result=str)
    def setKeyBinding(
        self,
        patient_id: str,
        gesture_id: str,
        key: str,
    ) -> str:
        """Bind a key to a gesture in a profile."""
        try:
            profile = self.profile_manager.set_key_binding(
                patient_id,
                gesture_id,
                key,
            )
            self.profilesChanged.emit()
            return self._success(self._profile_data(profile))
        except (OSError, ProfileError) as error:
            return self._failure(error)

    @Slot(str, str, result=str)
    def removeKeyBinding(self, patient_id: str, gesture_id: str) -> str:
        """Remove a keybind from a gesture in a profile."""
        try:
            profile = self.profile_manager.remove_key_binding(
                patient_id,
                gesture_id,
            )
            self.profilesChanged.emit()
            return self._success(self._profile_data(profile))
        except (OSError, ProfileError) as error:
            return self._failure(error)
