"""Unit tests for ProfileManager and PatientProfile models.

Each test uses a temporary directory so nothing in app/data/profiles/ is touched.
"""

import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from app.profile_manager import GameProfile, GestureBinding, PatientProfile, ProfileManager
from app.profile_manager.exceptions import (
    ProfileAlreadyExistsError,
    ProfileConflictError,
    ProfileNotFoundError,
    ProfileValidationError,
)


def _sample_profile() -> PatientProfile:
    return PatientProfile(
        patient_id="patient-a",
        patient_name="Patient A",
        game_profiles=[
            GameProfile(
                game_name="Celeste",
                gestures=[GestureBinding(name="Right Arm Raise", key="ArrowUp")],
            )
        ],
    )


class ProfileManagerTests(unittest.TestCase):
    """ProfileManager CRUD, validation, last-session, and game-profile operations."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = ProfileManager(Path(self.temp_dir.name))
        self.sample_profile = _sample_profile()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_and_load_round_trip(self) -> None:
        """Save then load a profile; patient id, schema version, and gesture data must match."""
        self.manager.save(self.sample_profile)
        loaded = self.manager.load("patient-a")

        self.assertEqual(loaded.patient_id, "patient-a")
        self.assertEqual(loaded.schema_version, 1)
        self.assertEqual(loaded.game_profiles[0].gestures[0].key, "ArrowUp")

    def test_create_rejects_duplicate_profile(self) -> None:
        """create() must raise ProfileAlreadyExistsError when the patient id is already taken."""
        self.manager.create(self.sample_profile)
        with self.assertRaises(ProfileAlreadyExistsError):
            self.manager.create(self.sample_profile)

    def test_list_profiles(self) -> None:
        """list_profiles() returns every saved profile with correct patient names."""
        self.manager.save(self.sample_profile)
        profiles = self.manager.list_profiles()

        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].patient_name, "Patient A")

    def test_duplicate_profile(self) -> None:
        """duplicate() copies game profiles to a new patient id and optional display name."""
        self.manager.save(self.sample_profile)
        duplicate = self.manager.duplicate("patient-a", "patient-a-copy", "Patient A Copy")

        self.assertEqual(duplicate.patient_id, "patient-a-copy")
        self.assertEqual(duplicate.patient_name, "Patient A Copy")
        self.assertEqual(self.manager.load("patient-a-copy").game_profiles[0].game_name, "Celeste")

    def test_delete_profile(self) -> None:
        """delete() removes the on-disk JSON file; load() must fail afterward."""
        self.manager.save(self.sample_profile)
        self.assertTrue(self.manager.exists("patient-a"))

        self.manager.delete("patient-a")

        self.assertFalse(self.manager.exists("patient-a"))
        with self.assertRaises(ProfileNotFoundError):
            self.manager.load("patient-a")

    def test_delete_missing_profile_raises(self) -> None:
        """delete() must raise ProfileNotFoundError when the patient id does not exist."""
        with self.assertRaises(ProfileNotFoundError):
            self.manager.delete("missing-profile")

    def test_load_missing_profile_raises(self) -> None:
        """load() must raise ProfileNotFoundError when no JSON file exists for that patient id."""
        with self.assertRaises(ProfileNotFoundError):
            self.manager.load("missing-profile")

    def test_invalid_json_raises_validation_error(self) -> None:
        """load() must raise ProfileValidationError when the on-disk file is not valid JSON."""
        bad_file = self.manager.profiles_dir / "broken.json"
        bad_file.write_text("{not valid json", encoding="utf-8")

        with self.assertRaises(ProfileValidationError):
            self.manager.load("broken")

    def test_patient_profile_requires_game_profiles(self) -> None:
        """PatientProfile model must reject an empty gameProfiles list at validation time."""
        with self.assertRaises(ValidationError):
            PatientProfile(patient_id="x", patient_name="X", game_profiles=[])

    def test_export_schema_includes_schema_version(self) -> None:
        """export_schema() JSON schema must document schemaVersion and lastSessionGame fields."""
        schema = self.manager.export_schema()
        self.assertIn("schemaVersion", schema.get("properties", {}))
        self.assertIn("lastSessionGame", schema.get("properties", {}))

    def test_record_and_load_last_session(self) -> None:
        """record_last_session() persists the game name; load_last_session() returns that game profile."""
        self.manager.save(self.sample_profile)
        updated = self.manager.record_last_session("patient-a", "Celeste")

        self.assertEqual(updated.last_session_game, "Celeste")
        profile, game = self.manager.load_last_session("patient-a")
        self.assertEqual(profile.patient_id, "patient-a")
        self.assertEqual(game.game_name, "Celeste")

    def test_load_last_session_without_history_raises(self) -> None:
        """load_last_session() must raise ProfileNotFoundError when lastSessionGame was never set."""
        self.manager.save(self.sample_profile)
        with self.assertRaises(ProfileNotFoundError):
            self.manager.load_last_session("patient-a")

    def test_add_game_profile(self) -> None:
        """add_game_profile() appends a new game configuration to an existing patient."""
        self.manager.save(self.sample_profile)
        new_game = GameProfile(
            game_name="Mario",
            gestures=[GestureBinding(name="Jump", key="Space")],
        )
        profile = self.manager.add_game_profile("patient-a", new_game)

        self.assertEqual(len(profile.game_profiles), 2)
        self.assertEqual(profile.game_profiles[1].game_name, "Mario")

    def test_add_duplicate_game_profile_raises(self) -> None:
        """add_game_profile() must raise ProfileConflictError when the game name already exists."""
        self.manager.save(self.sample_profile)
        duplicate_game = GameProfile(
            game_name="Celeste",
            gestures=[GestureBinding(name="Jump", key="Space")],
        )
        with self.assertRaises(ProfileConflictError):
            self.manager.add_game_profile("patient-a", duplicate_game)

    def test_update_game_profile(self) -> None:
        """update_game_profile() replaces gestures and can rename a game under the same patient."""
        self.manager.save(self.sample_profile)
        updated_game = GameProfile(
            game_name="Celeste — Rehab Mode",
            gestures=[GestureBinding(name="Squat", key="ArrowDown", threshold=0.8)],
        )
        profile = self.manager.update_game_profile("patient-a", "Celeste", updated_game)

        self.assertEqual(profile.game_profiles[0].game_name, "Celeste — Rehab Mode")
        self.assertEqual(profile.game_profiles[0].gestures[0].key, "ArrowDown")


if __name__ == "__main__":
    unittest.main()
