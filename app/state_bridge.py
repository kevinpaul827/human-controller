from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from .gesture_store import GestureStore
from .profile_manager import PatientProfile, ProfileManager
from .trigger_controller import DEFAULT_SETTINGS


DEFAULT_PATIENTS = (
    ("patient-a", "Patient A"),
    ("patient-b", "Patient B"),
)


class StateBridge(QObject):


    runtimeConfigurationChanged = Signal(dict)
    stateChanged = Signal(dict)

    def __init__(self, data_dir: Path, gesture_store: GestureStore):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.data_dir / "state.json"
        self.profile_manager = ProfileManager(self.data_dir / "profiles")
        self.gesture_store = gesture_store
        self._ensure_profiles()

    def _ensure_profiles(self) -> None:
        if self.profile_manager.list_profiles():
            return
        for patient_id, patient_name in DEFAULT_PATIENTS:
            self.profile_manager.create(
                PatientProfile(patientId=patient_id, patientName=patient_name)
            )

    def _read_ui_state(self) -> dict:
        defaults = {
            "presets": [],
            "activePresetId": None,
            "selectedPatientId": DEFAULT_PATIENTS[0][0],
            "pendingGestures": [],
            "settings": dict(DEFAULT_SETTINGS),
        }
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                defaults.update(payload)
        except (OSError, json.JSONDecodeError):
            pass
        defaults["settings"] = {**DEFAULT_SETTINGS, **defaults.get("settings", {})}
        return defaults

    def _write_ui_state(self, payload: dict) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.state_path)

    def _selected_profile(self, state: dict):
        profiles = self.profile_manager.list_profiles()
        selected_id = state.get("selectedPatientId")
        return next((p for p in profiles if p.patient_id == selected_id), profiles[0])

    def _snapshot(self) -> dict:
        ui = self._read_ui_state()
        profiles = self.profile_manager.list_profiles()
        selected = self._selected_profile(ui)
        recorded = []
        for gesture in self.gesture_store.load_all():
            path = self.gesture_store.gesture_path(gesture.gesture_id)
            calibrated_at = datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
            recorded.append(
                {
                    "gestureId": gesture.gesture_id,
                    "name": gesture.name,
                    "calibratedAt": calibrated_at,
                    "matchScore": None,
                }
            )
        recorded_ids = {item["gestureId"] for item in recorded}
        pending = [
            item for item in ui.get("pendingGestures", [])
            if item.get("gestureId") not in recorded_ids
        ]
        default_threshold = float(
            ui.get("settings", {}).get(
                "matchThreshold", DEFAULT_SETTINGS["matchThreshold"]
            )
        )
        return {
            "gestures": recorded + pending,
            "bindings": [
                {
                    "gestureId": gesture_id,
                    "key": key,
                    "matchThreshold": selected.match_thresholds.get(
                        gesture_id, default_threshold
                    ),
                }
                for gesture_id, key in selected.key_bindings.items()
            ],
            "presets": ui.get("presets", []),
            "patients": [
                {"patientId": profile.patient_id, "patientName": profile.patient_name}
                for profile in profiles
            ],
            "selectedPatientId": selected.patient_id,
            "activePresetId": ui.get("activePresetId"),
            "settings": ui.get("settings", dict(DEFAULT_SETTINGS)),
        }

    def runtime_configuration(self) -> dict:
        snapshot = self._snapshot()
        return {
            "bindings": {
                item["gestureId"]: item["key"] for item in snapshot["bindings"]
            },
            "matchThresholds": {
                item["gestureId"]: item["matchThreshold"]
                for item in snapshot["bindings"]
            },
            "settings": snapshot["settings"],
        }

    @Slot(result="QVariantMap")
    def getState(self):
        return self._snapshot()

    @Slot("QVariantMap", result="QVariantMap")
    def saveState(self, payload):
        current = self._read_ui_state()
        selected_id = str(payload.get("selectedPatientId") or current["selectedPatientId"])
        binding_items = [
            item for item in payload.get("bindings", [])
            if item.get("gestureId") and item.get("key")
        ]
        bindings = {
            str(item.get("gestureId")): str(item.get("key"))
            for item in binding_items
        }
        default_threshold = float(
            payload.get("settings", current.get("settings", {})).get(
                "matchThreshold", DEFAULT_SETTINGS["matchThreshold"]
            )
        )
        match_thresholds = {
            str(item.get("gestureId")): min(
                100.0,
                max(0.0, float(item.get("matchThreshold", default_threshold))),
            )
            for item in binding_items
        }
        profile = self.profile_manager.load(selected_id)
        profile.key_bindings = bindings
        profile.match_thresholds = match_thresholds
        self.profile_manager.save(profile)
        pending = [
            item for item in payload.get("gestures", []) if not item.get("calibratedAt")
        ]
        ui = {
            "presets": payload.get("presets", current.get("presets", [])),
            "activePresetId": payload.get("activePresetId"),
            "selectedPatientId": selected_id,
            "pendingGestures": pending,
            "settings": {**DEFAULT_SETTINGS, **payload.get("settings", {})},
        }
        self._write_ui_state(ui)
        snapshot = self._snapshot()
        self.runtimeConfigurationChanged.emit(self.runtime_configuration())
        self.stateChanged.emit(snapshot)
        return snapshot

    @Slot(str, result="QVariantMap")
    def selectPatient(self, patient_id):
        ui = self._read_ui_state()
        self.profile_manager.load(patient_id)
        ui["selectedPatientId"] = patient_id
        ui["activePresetId"] = None
        self._write_ui_state(ui)
        snapshot = self._snapshot()
        self.runtimeConfigurationChanged.emit(self.runtime_configuration())
        self.stateChanged.emit(snapshot)
        return snapshot

    @Slot(str, result="QVariantMap")
    def createProfile(self, patient_name):
        profile = self.profile_manager.create_new(str(patient_name).strip())
        ui = self._read_ui_state()
        ui["selectedPatientId"] = profile.patient_id
        ui["activePresetId"] = None
        self._write_ui_state(ui)
        snapshot = self._snapshot()
        self.runtimeConfigurationChanged.emit(self.runtime_configuration())
        self.stateChanged.emit(snapshot)
        return snapshot

    @Slot(str, result=bool)
    def deleteGesture(self, gesture_id):
        self.gesture_store.delete(gesture_id)
        for profile in self.profile_manager.list_profiles():
            if gesture_id in profile.key_bindings:
                del profile.key_bindings[gesture_id]
                profile.match_thresholds.pop(gesture_id, None)
                self.profile_manager.save(profile)
        return True
