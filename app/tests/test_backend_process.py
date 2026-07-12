import os
import sys
import unittest
from unittest.mock import patch

from app.backend_process import (
    BACKEND_HELPER_FLAG,
    BACKEND_RELOAD_FLAG,
    BACKEND_RUNNER_ENV,
    PROJECT_ROOT_ENV,
    build_backend_command,
)


class BackendProcessCommandTests(unittest.TestCase):
    def test_dev_backend_command_uses_python_module(self):
        command = build_backend_command({})

        self.assertEqual(command, [sys.executable, "-m", "backend.dev_server"])

    def test_frozen_backend_command_uses_bundled_executable(self):
        with patch.object(sys, "frozen", True, create=True):
            command = build_backend_command({})

        self.assertEqual(command, [sys.executable, BACKEND_HELPER_FLAG])

    def test_backend_reload_uses_repo_reloader_when_env_is_present(self):
        env = {
            BACKEND_RELOAD_FLAG: "1",
            BACKEND_RUNNER_ENV: "/tmp/dev-python",
            PROJECT_ROOT_ENV: "/tmp/human-controller",
        }

        with patch.object(sys, "frozen", True, create=True):
            command = build_backend_command(env)

        self.assertEqual(
            command,
            ["/tmp/dev-python", "/tmp/human-controller/scripts/run_backend_dev.py"],
        )


if __name__ == "__main__":
    unittest.main()
