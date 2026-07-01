from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CURRENT_SCHEMA_VERSION = 1


class GestureBinding(BaseModel):
    """One therapeutic movement mapped to a keyboard key."""

    name: str = Field(min_length=1, max_length=80)
    key: str = Field(min_length=1, max_length=32)
    threshold: float = Field(default=0.75, ge=0.0, le=1.0)


class GameProfile(BaseModel):
    """Gesture bindings for one game under a patient profile."""

    game_name: str = Field(min_length=1, max_length=80, alias="gameName")
    gestures: list[GestureBinding] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    @field_validator("gestures")
    @classmethod
    def gestures_must_not_be_empty(cls, value: list[GestureBinding]) -> list[GestureBinding]:
        if not value:
            raise ValueError("game profile must contain at least one gesture binding")
        return value


class PatientProfile(BaseModel):
    """Top-level patient configuration saved to disk."""

    schema_version: Literal[1] = Field(default=CURRENT_SCHEMA_VERSION, alias="schemaVersion")
    patient_id: str = Field(min_length=1, max_length=64, alias="patientId")
    patient_name: str = Field(min_length=1, max_length=80, alias="patientName")
    notes: str = ""
    last_session_game: str | None = Field(default=None, alias="lastSessionGame")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt")
    game_profiles: list[GameProfile] = Field(default_factory=list, alias="gameProfiles")

    model_config = {"populate_by_name": True}

    @field_validator("patient_id")
    @classmethod
    def patient_id_must_be_safe_filename(cls, value: str) -> str:
        if any(char in value for char in r'\/:*?"<>|'):
            raise ValueError("patient_id cannot contain path separators or invalid filename characters")
        return value

    @field_validator("game_profiles")
    @classmethod
    def game_profiles_must_not_be_empty(cls, value: list[GameProfile]) -> list[GameProfile]:
        if not value:
            raise ValueError("patient profile must contain at least one game profile")
        return value
