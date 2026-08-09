from __future__ import annotations

from pathlib import Path
from typing import Any

from ..bridges.bridge_types import GestureMatchPayload
from ..gestures.gesture_matcher import GestureMatcher
from ..gestures.gesture_store import GestureStore
from ..utils.logging_utils import log_info
from .key_injector import KeyInjectionError, KeyInjector
from .trigger_controller import TriggerController


class GestureSession:
    def __init__(
        self,
        gestures_dir: Path | None = None,
        key_injector: KeyInjector | None = None,
        *,
        matcher: GestureMatcher | None = None,
        trigger_controller: TriggerController | None = None,
    ) -> None:
        self.matcher = matcher or GestureMatcher(
            store=GestureStore(gestures_dir) if gestures_dir else GestureStore()
        )
        self.key_injector = key_injector or KeyInjector()
        self.trigger_controller = trigger_controller or TriggerController()
        self._loaded_gesture_ids: list[str] = []
        self._key_bindings: dict[str, str] = {}
        self._use_gesture_subset = False

    @property
    def store(self):
        return self.matcher.store

    @property
    def active_angle_keys(self):
        return self.matcher.active_angle_keys

    @property
    def bound_angle_keys(self):
        return self.matcher.bound_angle_keys

    def start(self) -> None:
        self.release_injected_keys()
        self.refresh_templates()
        self.trigger_controller.reset()

    def stop(self) -> None:
        self.release_injected_keys()
        self.trigger_controller.reset()

    def configure_runtime(
        self,
        bindings: dict[str, str],
        settings: dict[str, object],
        match_thresholds: dict[str, float],
    ) -> None:
        self.release_injected_keys()
        self._key_bindings = dict(bindings)
        self._loaded_gesture_ids = list(self._key_bindings)
        self._use_gesture_subset = True
        self.trigger_controller.configure(bindings, settings, match_thresholds)
        self.matcher.set_active_gestures(
            bindings.keys(),
            {
                gesture_id: threshold / 100.0
                for gesture_id, threshold in match_thresholds.items()
            },
        )
        self.matcher.match_threshold = (
            self.trigger_controller.settings["matchThreshold"] / 100.0
        )

    def process_pose(
        self,
        pose,
        active_angle_keys=None,
        *,
        inject_keys: bool,
    ) -> tuple[GestureMatchPayload, dict]:
        angles = self._angles_for_pose(pose, active_angle_keys)
        match_event = self.matcher.match_pose(pose, angles=angles)
        payload: GestureMatchPayload = match_event.to_dict()
        key_action = self.trigger_controller.process(payload)
        if key_action is None or not inject_keys:
            return payload, angles

        try:
            if key_action["action"] == "press":
                self.key_injector.press(key_action["key"])
                payload.update(
                    {
                        "triggered": True,
                        "key": key_action["key"],
                        "keyAction": "press",
                    }
                )
            else:
                self.key_injector.release(key_action["key"])
                payload.update(
                    {
                        "key": key_action["key"],
                        "keyAction": "release",
                    }
                )
        except KeyInjectionError as error:
            self.release_injected_keys()
            self.trigger_controller.reset()
            payload.update(
                {
                    "triggered": False,
                    "key": key_action["key"],
                    "injectionError": str(error),
                }
            )
        return payload, angles

    def refresh_templates(self) -> None:
        self.matcher.reload_templates()
        if self._use_gesture_subset:
            self.matcher.set_active_gestures(
                self._loaded_gesture_ids,
                self.matcher.match_thresholds,
            )
            return
        self.matcher.set_active_gestures(None)

    def list_saved_gestures(self):
        return self.store.list_gestures()

    def loaded_gestures(self):
        gestures = []
        for gesture_id in self._loaded_gesture_ids:
            try:
                gestures.append(self.store.load(gesture_id))
            except (OSError, ValueError, FileNotFoundError):
                continue
        return gestures

    def loaded_gesture_summaries(self):
        return [gesture.to_summary() for gesture in self.loaded_gestures()]

    def gesture_mappings(self):
        return [
            {
                **gesture.to_summary(),
                "key": self._key_bindings.get(gesture.gesture_id, ""),
            }
            for gesture in self.loaded_gestures()
        ]

    def configure_gestures(self, key_bindings):
        self._key_bindings = dict(key_bindings)
        self._loaded_gesture_ids = list(self._key_bindings)
        self._use_gesture_subset = True
        self.refresh_templates()
        return self.gesture_mappings()

    def clear_gestures(self) -> None:
        self._loaded_gesture_ids = []
        self._key_bindings = {}
        self._use_gesture_subset = False
        self.refresh_templates()

    def load_saved_gesture(self, gesture_id):
        resolved_gesture_id = str(gesture_id or "").strip()
        if not resolved_gesture_id:
            raise ValueError("Gesture ID is required.")

        gesture = self.store.load(resolved_gesture_id)
        if resolved_gesture_id not in self._key_bindings:
            raise ValueError(
                "Assign this movement a profile key binding before loading it "
                "for a session."
            )
        return {
            "gesture": gesture.to_summary(),
            "loadedGestures": self.loaded_gesture_summaries(),
        }

    def release_injected_keys(self) -> None:
        try:
            self.key_injector.release_all()
        except KeyInjectionError as error:
            log_info(f"[gesture_session] failed to release injected key: {error}")

    def _angles_for_pose(self, pose, active_angle_keys) -> dict:
        return self.matcher.angles_for_pose(pose, active_angle_keys)

    @staticmethod
    def reset_match_payload() -> GestureMatchPayload:
        return {
            "gestureId": None,
            "name": None,
            "score": 0.0,
            "timestamp": None,
            "matched": False,
            "hasTemplates": False,
            "triggered": False,
            "keyAction": "reset",
        }
