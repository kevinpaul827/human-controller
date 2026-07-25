import unittest
from unittest.mock import patch

import run_app


class RunAppTests(unittest.TestCase):
    @patch("run_app.smoke_imports")
    def test_smoke_flag_runs_dependency_check_without_starting_ui(self, smoke):
        with patch.object(run_app.sys, "argv", ["run_app.py", run_app.SMOKE_IMPORTS_FLAG]):
            with patch("run_app.app_main") as app_main:
                run_app.main()

        smoke.assert_called_once_with()
        app_main.assert_not_called()


if __name__ == "__main__":
    unittest.main()
