"""runtime_configuration.py

Validates and normalizes runtime settings,
gesture bindings, and match thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from backend.perception.models import normalize_pose_model

from .trigger_controller import DEFAULT_SETTINGS
from ..utils.validation import bounded_number


def _mapping(value: object) -> Mapping[object, object]:
    return value if isinstance(value, Mapping) else {}


@dataclass(frozen=True)
class RuntimeConfiguration:
    settings: dict[str, object]
    bindings: dict[str, str]
    match_thresholds: dict[str, float]

    @classmethod
    def from_payload(cls, payload: object) -> "RuntimeConfiguration":
        configuration = _mapping(payload)
        raw_settings = _mapping(configuration.get("settings"))
        settings: dict[str, object] = {
            "matchThreshold": bounded_number(
                raw_settings.get("matchThreshold"),
                float(DEFAULT_SETTINGS["matchThreshold"]),
                0.0,
                100.0,
            ),
            "cooldown": bounded_number(
                raw_settings.get("cooldown"),
                float(DEFAULT_SETTINGS["cooldown"]),
                0.0,
                10.0,
            ),
            "smoothing": int(
                bounded_number(
                    raw_settings.get("smoothing"),
                    float(DEFAULT_SETTINGS["smoothing"]),
                    0.0,
                    4.0,
                )
            ),
            "poseModel": normalize_pose_model(raw_settings.get("poseModel")),
        }

        bindings = {
            str(gesture_id): str(key)
            for gesture_id, key in _mapping(configuration.get("bindings")).items()
            if str(gesture_id).strip() and str(key).strip()
        }
        default_threshold = float(settings["matchThreshold"])
        match_thresholds = {
            str(gesture_id): bounded_number(
                threshold,
                default_threshold,
                0.0,
                100.0,
            )
            for gesture_id, threshold in _mapping(
                configuration.get("matchThresholds")
            ).items()
            if str(gesture_id).strip()
        }
        return cls(settings, bindings, match_thresholds)
