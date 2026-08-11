"""run_app.py

This is the executable entry point for the Human Controller
app. It supports the following command-line modes:

- PIP_HELPER_FLAG: starts macOS picture-in-picture helper.
- BACKEND_HELPER_FLAG: starts backend health-server helper.
- SMOKE_IMPORTS_FLAG: verifies MediaPipe and its native runtime load.
- SMOKE_BROWSER_INPUT_FLAG: runs browser-input smoke test.
"""
import sys

from devtools.backend_process import BACKEND_HELPER_FLAG
from app.pip_protocol import PIP_HELPER_FLAG

# Command-line modes for smoke tests
SMOKE_IMPORTS_FLAG = "--smoke-imports"
SMOKE_BROWSER_INPUT_FLAG = "--smoke-browser-input"


def _load_current_mediapipe_native_runtime():
    """Load native runtime used by current MediaPipe installations."""
    import mediapipe.tasks.c
    from mediapipe.tasks.python.core import mediapipe_c_bindings

    mediapipe_c_bindings.load_raw_library()


def _load_legacy_mediapipe_native_runtime():
    """Load and validate native runtime used by legacy MediaPipe versions."""
    import mediapipe.python._framework_bindings as framework_bindings

    if not getattr(framework_bindings, "__file__", None):
        raise RuntimeError("Bundled MediaPipe native extension is missing.")


def _load_mediapipe_native_runtime():
    """Load available MediaPipe native runtime."""
    try:
        _load_current_mediapipe_native_runtime()
    except ModuleNotFoundError as error:
        if error.name != "mediapipe.tasks.c":
            raise
        _load_legacy_mediapipe_native_runtime()


def smoke_imports():
    """Verify required MediaPipe Python and native components can load."""
    from mediapipe.tasks.python.vision import (
        PoseLandmarker,
        PoseLandmarkerOptions,
        RunningMode,
    )

    _load_mediapipe_native_runtime()


def main():
    """Execute with command line modes or start main application."""
    if PIP_HELPER_FLAG in sys.argv[1:]:
        from app.platforms.macos.pip_helper import run_pip_helper_from_argv

        flag_index = sys.argv.index(PIP_HELPER_FLAG)
        raise SystemExit(
            run_pip_helper_from_argv(sys.argv[flag_index + 1 :])
        )

    if BACKEND_HELPER_FLAG in sys.argv[1:]:
        from devtools.backend_health_server import main as backend_main

        backend_main()
        return

    if SMOKE_IMPORTS_FLAG in sys.argv[1:]:
        smoke_imports()
        return

    if SMOKE_BROWSER_INPUT_FLAG in sys.argv[1:]:
        from devtools.browser_input_smoke import run_browser_input_smoke

        flag_index = sys.argv.index(SMOKE_BROWSER_INPUT_FLAG)
        try:
            result_path = sys.argv[flag_index + 1]
        except IndexError as exc:
            raise RuntimeError(
                f"{SMOKE_BROWSER_INPUT_FLAG} requires an output path"
            ) from exc
        raise SystemExit(run_browser_input_smoke(result_path))

    from app.main import main as app_main

    app_main()


if __name__ == "__main__":
    main()
