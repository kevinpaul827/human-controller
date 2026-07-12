import sys
import unittest
from unittest.mock import Mock, patch

from app.backend_process import (
    BACKEND_HELPER_FLAG,
    BACKEND_RELOAD_FLAG,
    BACKEND_RUNNER_ENV,
    PROJECT_ROOT_ENV,
    BackendProcessManager,
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

    @patch("app.backend_process.subprocess.run")
    def test_windows_stop_terminates_the_backend_process_tree(self, run):
        manager = BackendProcessManager()
        process = Mock(pid=1234)
        process.poll.return_value = None
        manager.process = process

        with patch("app.backend_process.os.name", "nt"):
            manager.stop()

        run.assert_called_once_with(
            ["taskkill", "/PID", "1234", "/T", "/F"],
            check=False,
            stdout=-3,
            stderr=-3,
        )
        process.wait.assert_called_once_with(timeout=5)


if __name__ == "__main__":
    unittest.main()
