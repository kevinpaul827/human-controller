"""Unit tests for schema v2 ProfileManager gesture key bindings."""

import json
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from app.profile_manager import PatientProfile, ProfileManager
from app.profile_manager.exceptions import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ProfileValidationError,
)


def _sample_profile() -> PatientProfile:
    return PatientProfile(
        patient_id="patient-a",
        patient_name="Patient A",
        key_bindings={
            "gesture1": "ArrowUp",
            "elbow_bend": "A",
        },
    )


class ProfileManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = ProfileManager(Path(self.temp_dir.name))
        self.sample_profile = _sample_profile()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_and_load_round_trip(self) -> None:
        self.manager.save(self.sample_profile)
        loaded = self.manager.load("patient-a")

        self.assertEqual(loaded.patient_id, "patient-a")
        self.assertEqual(loaded.schema_version, 2)
        self.assertEqual(loaded.key_bindings["gesture1"], "ArrowUp")

    def test_saved_json_uses_key_bindings_alias(self) -> None:
        path = self.manager.save(self.sample_profile)
        payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["schemaVersion"], 2)
        self.assertEqual(payload["keyBindings"]["elbow_bend"], "A")
        self.assertNotIn("gameProfiles", payload)

    def test_create_rejects_duplicate_profile(self) -> None:
        self.manager.create(self.sample_profile)
        with self.assertRaises(ProfileAlreadyExistsError):
            self.manager.create(self.sample_profile)

    def test_create_new_generates_uuid_and_preserves_schema_version(self) -> None:
        created = self.manager.create_new("New Patient", "Initial assessment")

        self.assertEqual(str(UUID(created.patient_id)), created.patient_id)
        self.assertEqual(created.schema_version, 2)
        self.assertEqual(created.patient_name, "New Patient")
        self.assertEqual(created.notes, "Initial assessment")
        self.assertTrue(self.manager.exists(created.patient_id))

    def test_create_new_generates_unique_patient_ids(self) -> None:
        first = self.manager.create_new("Patient")
        second = self.manager.create_new("Patient")

        self.assertNotEqual(first.patient_id, second.patient_id)

    def test_list_profiles(self) -> None:
        self.manager.save(self.sample_profile)
        profiles = self.manager.list_profiles()

        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].patient_name, "Patient A")

    def test_duplicate_profile_copies_key_bindings(self) -> None:
        self.manager.save(self.sample_profile)
        duplicate = self.manager.duplicate(
            "patient-a",
            "patient-a-copy",
            "Patient A Copy",
        )

        self.assertEqual(duplicate.patient_id, "patient-a-copy")
        self.assertEqual(duplicate.patient_name, "Patient A Copy")
        self.assertEqual(duplicate.key_bindings, self.sample_profile.key_bindings)

    def test_duplicate_profile_rejects_unsafe_patient_id(self) -> None:
        self.manager.save(self.sample_profile)
        escaped_path = self.manager.profiles_dir.parent / "escaped.json"

        with self.assertRaises(ProfileValidationError):
            self.manager.duplicate("patient-a", "../escaped")

        self.assertFalse(escaped_path.exists())

    def test_delete_profile(self) -> None:
        self.manager.save(self.sample_profile)
        self.manager.delete("patient-a")

        self.assertFalse(self.manager.exists("patient-a"))
        with self.assertRaises(ProfileNotFoundError):
            self.manager.load("patient-a")

    def test_delete_missing_profile_raises(self) -> None:
        with self.assertRaises(ProfileNotFoundError):
            self.manager.delete("missing-profile")

    def test_load_missing_profile_raises(self) -> None:
        with self.assertRaises(ProfileNotFoundError):
            self.manager.load("missing-profile")

    def test_invalid_json_raises_validation_error(self) -> None:
        bad_file = self.manager.profiles_dir / "broken.json"
        bad_file.write_text("{not valid json", encoding="utf-8")

        with self.assertRaises(ProfileValidationError):
            self.manager.load("broken")

    def test_schema_v1_profile_is_rejected_with_clear_error(self) -> None:
        old_profile = self.manager.profiles_dir / "legacy.json"
        old_profile.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "patientId": "legacy",
                    "patientName": "Legacy",
                    "gameProfiles": [],
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ProfileValidationError,
            "unsupported schema version 1",
        ):
            self.manager.load("legacy")

    def test_profile_allows_empty_key_bindings(self) -> None:
        profile = PatientProfile(
            patient_id="new-patient",
            patient_name="New Patient",
        )
        self.assertEqual(profile.key_bindings, {})

    def test_profile_rejects_empty_gesture_id(self) -> None:
        with self.assertRaises(ValidationError):
            PatientProfile(
                patient_id="patient-a",
                patient_name="Patient A",
                key_bindings={"": "A"},
            )

    def test_profile_rejects_empty_key(self) -> None:
        with self.assertRaises(ValidationError):
            PatientProfile(
                patient_id="patient-a",
                patient_name="Patient A",
                key_bindings={"gesture1": ""},
            )

    def test_profile_rejects_legacy_game_profiles_field(self) -> None:
        with self.assertRaises(ValidationError):
            PatientProfile(
                patient_id="patient-a",
                patient_name="Patient A",
                game_profiles=[],
            )

    def test_set_key_binding_adds_and_updates_mapping(self) -> None:
        self.manager.save(self.sample_profile)

        added = self.manager.set_key_binding(
            "patient-a",
            "squat",
            "ArrowDown",
        )
        updated = self.manager.set_key_binding(
            "patient-a",
            "gesture1",
            "W",
        )

        self.assertEqual(added.key_bindings["squat"], "ArrowDown")
        self.assertEqual(updated.key_bindings["gesture1"], "W")
        self.assertEqual(
            self.manager.load("patient-a").key_bindings["gesture1"],
            "W",
        )

    def test_set_key_binding_rejects_invalid_key(self) -> None:
        self.manager.save(self.sample_profile)
        with self.assertRaises(ProfileValidationError):
            self.manager.set_key_binding("patient-a", "gesture1", " ")

    def test_remove_key_binding(self) -> None:
        self.manager.save(self.sample_profile)
        updated = self.manager.remove_key_binding("patient-a", "gesture1")

        self.assertNotIn("gesture1", updated.key_bindings)
        self.assertNotIn(
            "gesture1",
            self.manager.load("patient-a").key_bindings,
        )

    def test_remove_missing_key_binding_raises(self) -> None:
        self.manager.save(self.sample_profile)
        with self.assertRaises(ProfileNotFoundError):
            self.manager.remove_key_binding("patient-a", "missing")

    def test_export_schema_includes_key_bindings(self) -> None:
        schema = self.manager.export_schema()
        properties = schema.get("properties", {})

        self.assertIn("schemaVersion", properties)
        self.assertIn("keyBindings", properties)
        self.assertNotIn("gameProfiles", properties)

    def test_only_schema_version_two_is_supported(self) -> None:
        self.assertTrue(self.manager.supports_schema_version(2))
        self.assertFalse(self.manager.supports_schema_version(1))


if __name__ == "__main__":
    unittest.main()
