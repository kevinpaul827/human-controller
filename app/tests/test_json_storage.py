import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.json_storage import json_path, write_json_atomic


class JsonStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_json_path_accepts_application_identifiers(self) -> None:
        path = json_path(
            self.directory,
            "patient-a_2.0",
            label="Patient ID",
        )

        self.assertEqual(path, self.directory / "patient-a_2.0.json")

    def test_json_path_rejects_empty_and_escaping_identifiers(self) -> None:
        for identifier in ("", "..", "../outside", "folder/item", "name\\item"):
            with self.subTest(identifier=identifier):
                with self.assertRaises(ValueError):
                    json_path(self.directory, identifier, label="Record ID")

    def test_atomic_write_round_trips_json_and_leaves_no_temporary_file(self) -> None:
        destination = self.directory / "state.json"

        write_json_atomic(destination, {"ready": True, "count": 2})

        self.assertEqual(
            json.loads(destination.read_text(encoding="utf-8")),
            {"ready": True, "count": 2},
        )
        self.assertEqual(list(self.directory.glob("*.tmp")), [])

    def test_failed_replace_preserves_existing_file_and_cleans_up(self) -> None:
        destination = self.directory / "state.json"
        destination.write_text('{"ready": false}', encoding="utf-8")

        with patch("pathlib.Path.replace", side_effect=OSError("disk error")):
            with self.assertRaisesRegex(OSError, "disk error"):
                write_json_atomic(destination, {"ready": True})

        self.assertEqual(destination.read_text(encoding="utf-8"), '{"ready": false}')
        self.assertEqual(list(self.directory.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
