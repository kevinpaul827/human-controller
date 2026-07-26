import sys

from app.main import main as app_main
from backend.dev_server import main as backend_main


BACKEND_HELPER_FLAG = "--backend-helper"
SMOKE_IMPORTS_FLAG = "--smoke-imports"
SMOKE_BROWSER_INPUT_FLAG = "--smoke-browser-input"


def smoke_imports():

    from importlib.resources import files

    import mediapipe.tasks.c
    from mediapipe.tasks.python.vision import (
        PoseLandmarker,
        PoseLandmarkerOptions,
        RunningMode,
    )

    native_library = files("mediapipe.tasks.c").joinpath("libmediapipe.dylib")
    if not native_library.is_file():
        raise RuntimeError(f"Bundled MediaPipe library is missing: {native_library}")


def main():
    if BACKEND_HELPER_FLAG in sys.argv[1:]:
        backend_main()
        return

    if SMOKE_IMPORTS_FLAG in sys.argv[1:]:
        smoke_imports()
        return

    if SMOKE_BROWSER_INPUT_FLAG in sys.argv[1:]:
        from app.browser_input_smoke import run_browser_input_smoke

        flag_index = sys.argv.index(SMOKE_BROWSER_INPUT_FLAG)
        try:
            result_path = sys.argv[flag_index + 1]
        except IndexError as exc:
            raise RuntimeError(
                f"{SMOKE_BROWSER_INPUT_FLAG} requires an output path"
            ) from exc
        raise SystemExit(run_browser_input_smoke(result_path))

    app_main()


if __name__ == "__main__":
    main()
