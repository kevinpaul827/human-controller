from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from .exceptions import (
    ProfileAlreadyExistsError,
    ProfileConflictError,
    ProfileNotFoundError,
    ProfileValidationError,
)
from .models import CURRENT_SCHEMA_VERSION, GameProfile, PatientProfile


class ProfileManager:
    """Save, load, list, duplicate, and delete versioned patient profiles."""

    def __init__(self, profiles_dir: str | Path) -> None:
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _profile_path(self, patient_id: str) -> Path:
        return self.profiles_dir / f"{patient_id}.json"

    def exists(self, patient_id: str) -> bool:
        return self._profile_path(patient_id).exists()

    def save(self, profile: PatientProfile) -> Path:
        profile.updated_at = datetime.now(timezone.utc)
        path = self._profile_path(profile.patient_id)
        payload = profile.model_dump(mode="json", by_alias=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def create(self, profile: PatientProfile) -> PatientProfile:
        if self.exists(profile.patient_id):
            raise ProfileAlreadyExistsError(f"Profile already exists: {profile.patient_id}")
        self.save(profile)
        return profile

    def load(self, patient_id: str) -> PatientProfile:
        path = self._profile_path(patient_id)
        if not path.exists():
            raise ProfileNotFoundError(f"Profile not found: {patient_id}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return PatientProfile.model_validate(data)
        except json.JSONDecodeError as exc:
            raise ProfileValidationError(f"Invalid JSON in profile '{patient_id}'") from exc
        except ValidationError as exc:
            raise ProfileValidationError(f"Profile '{patient_id}' failed validation") from exc

    def list_profiles(self) -> list[PatientProfile]:
        profiles: list[PatientProfile] = []
        for path in sorted(self.profiles_dir.glob("*.json")):
            patient_id = path.stem
            try:
                profiles.append(self.load(patient_id))
            except ProfileValidationError:
                continue
        return profiles

    def duplicate(self, patient_id: str, new_patient_id: str, new_patient_name: str | None = None) -> PatientProfile:
        if self.exists(new_patient_id):
            raise ProfileAlreadyExistsError(f"Profile already exists: {new_patient_id}")

        source = self.load(patient_id)
        duplicate_profile = source.model_copy(
            update={
                "patient_id": new_patient_id,
                "patient_name": new_patient_name or f"{source.patient_name} (Copy)",
                "last_session_game": source.last_session_game,
            }
        )
        self.save(duplicate_profile)
        return duplicate_profile

    def delete(self, patient_id: str) -> None:
        path = self._profile_path(patient_id)
        if not path.exists():
            raise ProfileNotFoundError(f"Profile not found: {patient_id}")
        path.unlink()

    def record_last_session(self, patient_id: str, game_name: str) -> PatientProfile:
        profile = self.load(patient_id)
        if not any(game.game_name == game_name for game in profile.game_profiles):
            raise ProfileNotFoundError(f"Game profile not found: {game_name}")

        profile.last_session_game = game_name
        self.save(profile)
        return profile

    def load_last_session(self, patient_id: str) -> tuple[PatientProfile, GameProfile]:
        profile = self.load(patient_id)
        if not profile.last_session_game:
            raise ProfileNotFoundError("No last session recorded for this patient")

        for game in profile.game_profiles:
            if game.game_name == profile.last_session_game:
                return profile, game

        raise ProfileNotFoundError(
            f"Last session game '{profile.last_session_game}' is no longer available"
        )

    def add_game_profile(self, patient_id: str, game_profile: GameProfile) -> PatientProfile:
        profile = self.load(patient_id)
        if any(game.game_name == game_profile.game_name for game in profile.game_profiles):
            raise ProfileConflictError(f"Game profile already exists: {game_profile.game_name}")

        profile.game_profiles.append(game_profile)
        self.save(profile)
        return profile

    def update_game_profile(
        self,
        patient_id: str,
        current_game_name: str,
        updated_game_profile: GameProfile,
    ) -> PatientProfile:
        profile = self.load(patient_id)
        index = next(
            (idx for idx, game in enumerate(profile.game_profiles) if game.game_name == current_game_name),
            None,
        )
        if index is None:
            raise ProfileNotFoundError(f"Game profile not found: {current_game_name}")

        renamed = updated_game_profile.game_name != current_game_name
        if renamed and any(game.game_name == updated_game_profile.game_name for game in profile.game_profiles):
            raise ProfileConflictError(f"Game profile already exists: {updated_game_profile.game_name}")

        if profile.last_session_game == current_game_name and renamed:
            profile.last_session_game = updated_game_profile.game_name

        profile.game_profiles[index] = updated_game_profile
        self.save(profile)
        return profile

    def export_schema(self) -> dict:
        return PatientProfile.model_json_schema()

    def supports_schema_version(self, version: int) -> bool:
        return version == CURRENT_SCHEMA_VERSION
