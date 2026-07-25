from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CURRENT_SCHEMA_VERSION = 2


class PatientProfile(BaseModel):


    schema_version: Literal[2] = Field(
        default=CURRENT_SCHEMA_VERSION,
        alias="schemaVersion",
    )
    patient_id: str = Field(min_length=1, max_length=64, alias="patientId")
    patient_name: str = Field(min_length=1, max_length=80, alias="patientName")
    notes: str = ""
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        alias="updatedAt",
    )
    key_bindings: dict[str, str] = Field(
        default_factory=dict,
        alias="keyBindings",
    )
    match_thresholds: dict[str, float] = Field(
        default_factory=dict,
        alias="matchThresholds",
    )

    model_config = {
        "populate_by_name": True,
        "extra": "forbid",
    }

    @field_validator("patient_id")
    @classmethod
    def patient_id_must_be_safe_filename(cls, value: str) -> str:
        if any(char in value for char in r'\/:*?"<>|'):
            raise ValueError(
                "patient_id cannot contain path separators or invalid "
                "filename characters"
            )
        return value

    @field_validator("key_bindings")
    @classmethod
    def key_bindings_must_be_valid(
        cls,
        value: dict[str, str],
    ) -> dict[str, str]:
        validated: dict[str, str] = {}
        for gesture_id, key in value.items():
            resolved_gesture_id = gesture_id.strip()
            resolved_key = key.strip()
            if not resolved_gesture_id:
                raise ValueError("gesture_id cannot be empty")
            if len(resolved_gesture_id) > 64:
                raise ValueError("gesture_id cannot exceed 64 characters")
            if not resolved_key:
                raise ValueError("key binding cannot be empty")
            if len(resolved_key) > 32:
                raise ValueError("key binding cannot exceed 32 characters")
            validated[resolved_gesture_id] = resolved_key
        return validated

    @field_validator("match_thresholds")
    @classmethod
    def match_thresholds_must_be_valid(
        cls,
        value: dict[str, float],
    ) -> dict[str, float]:
        validated: dict[str, float] = {}
        for gesture_id, threshold in value.items():
            resolved_gesture_id = gesture_id.strip()
            if not resolved_gesture_id:
                raise ValueError("gesture_id cannot be empty")
            if len(resolved_gesture_id) > 64:
                raise ValueError("gesture_id cannot exceed 64 characters")
            resolved_threshold = float(threshold)
            if not 0.0 <= resolved_threshold <= 100.0:
                raise ValueError("match threshold must be between 0 and 100")
            validated[resolved_gesture_id] = resolved_threshold
        return validated
