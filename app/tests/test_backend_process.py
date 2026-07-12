import sys
import unittest
from unittest.mock import patch

from app.backend_process import BACKEND_HELPER_FLAG, build_backend_command


class BackendProcessCommandTests(unittest.TestCase):
    def test_dev_backend_command_uses_python_module(self):
        command = build_backend_command()

        self.assertEqual(command, [sys.executable, "-m", "backend.dev_server"])

    def test_frozen_backend_command_uses_bundled_executable(self):
        with patch.object(sys, "frozen", True, create=True):
            command = build_backend_command()

        self.assertEqual(command, [sys.executable, BACKEND_HELPER_FLAG])


if __name__ == "__main__":
    unittest.main()
