import unittest
from types import ModuleType
from unittest.mock import MagicMock, patch

import run_app


class RunAppTests(unittest.TestCase):
    @patch("run_app._load_legacy_mediapipe_native_runtime")
    @patch("run_app._load_current_mediapipe_native_runtime")
    def test_native_runtime_loads_current_mediapipe_c_library(
        self,
        load_current,
        load_legacy,
    ):
        run_app._load_mediapipe_native_runtime()

        load_current.assert_called_once_with()
        load_legacy.assert_not_called()

    @patch("run_app._load_legacy_mediapipe_native_runtime")
    @patch("run_app._load_current_mediapipe_native_runtime")
    def test_native_runtime_supports_legacy_framework_bindings(
        self,
        load_current,
        load_legacy,
    ):
        load_current.side_effect = ModuleNotFoundError(
            name="mediapipe.tasks.c"
        )

        run_app._load_mediapipe_native_runtime()

        load_current.assert_called_once_with()
        load_legacy.assert_called_once_with()

    @patch("run_app._load_legacy_mediapipe_native_runtime")
    @patch("run_app._load_current_mediapipe_native_runtime")
    def test_native_runtime_does_not_mask_broken_current_layout(
        self,
        load_current,
        load_legacy,
    ):
        import_error = ModuleNotFoundError(name="missing_dependency")
        load_current.side_effect = import_error

        with self.assertRaises(ModuleNotFoundError) as context:
            run_app._load_mediapipe_native_runtime()

        self.assertIs(context.exception, import_error)
        load_current.assert_called_once_with()
        load_legacy.assert_not_called()

    def test_native_runtime_rejects_missing_legacy_extension(
        self,
    ):
        mediapipe = ModuleType("mediapipe")
        mediapipe.__path__ = []
        mediapipe_python = ModuleType("mediapipe.python")
        mediapipe_python.__path__ = []
        framework_bindings = ModuleType(
            "mediapipe.python._framework_bindings"
        )

        with (
            patch.dict(
                run_app.sys.modules,
                {
                    "mediapipe": mediapipe,
                    "mediapipe.python": mediapipe_python,
                    "mediapipe.python._framework_bindings": framework_bindings,
                },
            ),
            self.assertRaisesRegex(
                RuntimeError,
                "native extension is missing",
            ),
        ):
            run_app._load_legacy_mediapipe_native_runtime()

    @patch("run_app.smoke_imports")
    def test_smoke_flag_runs_dependency_check_without_starting_ui(self, smoke):
        with patch.object(run_app.sys, "argv", ["run_app.py", run_app.SMOKE_IMPORTS_FLAG]):
            run_app.main()

        smoke.assert_called_once_with()

    @patch("app.dev.browser_input_smoke.run_browser_input_smoke", return_value=0)
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
            with self.assertRaises(SystemExit) as context:
                run_app.main()

        self.assertEqual(context.exception.code, 0)
        browser_smoke.assert_called_once_with("/tmp/browser-smoke.json")

    def test_pip_helper_flag_routes_without_starting_main_ui(self):
        helper_module = ModuleType("app.platforms.macos.pip_helper")
        helper_module.run_pip_helper_from_argv = MagicMock(return_value=0)
        arguments = [
            "run_app.py",
            run_app.PIP_HELPER_FLAG,
            "--frame-file",
            "/tmp/frame-map",
            "--parent-pid",
            "123",
        ]

        with (
            patch.dict(
                run_app.sys.modules,
                {"app.platforms.macos.pip_helper": helper_module},
            ),
            patch.object(run_app.sys, "argv", arguments),
            self.assertRaises(SystemExit) as context,
        ):
            run_app.main()

        self.assertEqual(context.exception.code, 0)
        helper_module.run_pip_helper_from_argv.assert_called_once_with(
            arguments[2:]
        )

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
