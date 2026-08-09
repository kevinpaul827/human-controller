from __future__ import annotations

import time
from collections import deque
from typing import Callable

from ..utils.validation import bounded_number


DEFAULT_SETTINGS = {
    "matchThreshold": 75.0,
    "cooldown": 0.5,
    "smoothing": 2,
    "poseModel": "lite",
}

KEY_TAP_SECONDS = 0.05


class TriggerController:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self.bindings: dict[str, str] = {}
        self.match_thresholds: dict[str, float] = {}
        self.settings = dict(DEFAULT_SETTINGS)
        self._candidate_id: str | None = None
        self._scores: deque[float] = deque(maxlen=3)
        self._active_gesture_id: str | None = None
        self._active_key: str | None = None
        self._active_pressed_at = float("-inf")
        self._latched_gesture_id: str | None = None
        self._last_triggered_at = float("-inf")

    def configure(
        self,
        bindings: dict[str, str],
        settings: dict | None = None,
        match_thresholds: dict[str, float] | None = None,
    ) -> None:
        self.bindings = {str(k): str(v) for k, v in bindings.items() if k and v}
        if settings:
            self.settings = {
                "matchThreshold": bounded_number(
                    settings.get("matchThreshold"), 75.0, 0.0, 100.0
                ),
                "cooldown": bounded_number(
                    settings.get("cooldown"), 0.5, 0.0, 10.0
                ),
                "smoothing": int(
                    bounded_number(settings.get("smoothing"), 2.0, 0.0, 4.0)
                ),
            }
        self.match_thresholds = {
            str(gesture_id): bounded_number(
                threshold,
                self.settings["matchThreshold"],
                0.0,
                100.0,
            )
            for gesture_id, threshold in (match_thresholds or {}).items()
            if gesture_id
        }
        self.reset()

    def reset(self) -> None:
        self._candidate_id = None
        self._scores.clear()
        self._active_gesture_id = None
        self._active_key = None
        self._active_pressed_at = float("-inf")
        self._latched_gesture_id = None

    def _clear_candidate(self) -> None:
        self._candidate_id = None
        self._scores.clear()

    def _release_active(self) -> dict | None:
        if self._active_key is None:
            return None
        if self.clock() - self._active_pressed_at < KEY_TAP_SECONDS:
            return None
        action = {
            "action": "release",
            "gestureId": self._active_gesture_id,
            "key": self._active_key,
        }
        self._active_gesture_id = None
        self._active_key = None
        self._active_pressed_at = float("-inf")
        self._clear_candidate()
        return action

    def process(self, match: dict) -> dict | None:
        now = self.clock()
        if (
            self._active_key is not None
            and now - self._active_pressed_at >= KEY_TAP_SECONDS
        ):
            return self._release_active()

        gesture_id = match.get("gestureId")
        score = bounded_number(match.get("score"), 0.0, 0.0, 1.0) * 100.0
        threshold = self.match_thresholds.get(
            str(gesture_id), self.settings["matchThreshold"]
        )

        if not match.get("matched") or not gesture_id or score < threshold:
            self._latched_gesture_id = None
            release = self._release_active()
            if release is not None:
                return release
            self._clear_candidate()
            return None

        key = self.bindings.get(str(gesture_id))
        if not key:
            release = self._release_active()
            if release is not None:
                return release
            self._clear_candidate()
            return None

        if (
            self._active_gesture_id is None
            and self._latched_gesture_id == str(gesture_id)
        ):
            self._clear_candidate()
            return None

        if self._active_gesture_id is not None:
            if self._active_gesture_id == str(gesture_id) and self._active_key == key:
                return None
            return self._release_active()

        if gesture_id != self._candidate_id:
            self._candidate_id = str(gesture_id)
            window = max(1, int(self.settings["smoothing"]) + 1)
            self._scores = deque(maxlen=window)
        self._scores.append(score)

        smoothed_score = sum(self._scores) / len(self._scores)
        if smoothed_score < threshold:
            self._clear_candidate()
            return None
        if now - self._last_triggered_at < self.settings["cooldown"]:
            return None

        self._active_gesture_id = str(gesture_id)
        self._active_key = key
        self._active_pressed_at = now
        self._latched_gesture_id = str(gesture_id)
        self._last_triggered_at = now
        return {
            "action": "press",
            "gestureId": str(gesture_id),
            "key": key,
            "score": smoothed_score / 100.0,
        }
