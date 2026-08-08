import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils.app_paths import DATA_DIR_ENV, user_data_dir


class AppPathsTests(unittest.TestCase):
    def test_environment_override_is_created_and_used(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "desktop-data"
            with patch.dict("os.environ", {DATA_DIR_ENV: str(target)}):
                self.assertEqual(user_data_dir(), target)
                self.assertTrue(target.is_dir())


if __name__ == "__main__":
    unittest.main()
