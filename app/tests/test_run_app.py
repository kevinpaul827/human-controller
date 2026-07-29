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

    @patch("app.browser_input_smoke.run_browser_input_smoke", return_value=0)
    def test_browser_smoke_flag_routes_to_browser_check(self, browser_smoke):
        with patch.object(
            run_app.sys,
            "argv",
            [
                "run_app.py",
                run_app.SMOKE_BROWSER_INPUT_FLAG,
                "/tmp/browser-smoke.json",
            ],
        ):
            with patch("run_app.app_main") as app_main:
                with self.assertRaises(SystemExit) as context:
                    run_app.main()

        self.assertEqual(context.exception.code, 0)
        browser_smoke.assert_called_once_with("/tmp/browser-smoke.json")
        app_main.assert_not_called()

    def test_browser_smoke_flag_requires_output_path(self):
        with patch.object(
            run_app.sys,
            "argv",
            ["run_app.py", run_app.SMOKE_BROWSER_INPUT_FLAG],
        ):
            with self.assertRaisesRegex(RuntimeError, "requires an output path"):
                run_app.main()


if __name__ == "__main__":
    unittest.main()
