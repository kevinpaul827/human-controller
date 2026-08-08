import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
FRONTEND_DIR = ROOT / "frontend"
PYINSTALLER_CONFIG_DIR = ROOT / ".pyinstaller"
SPEC_PATH = ROOT / "human_controller.spec"
FRONTEND_PATH = ROOT / "frontend" / "dist" / "index.html"
POSE_MODEL_NAMES = (
    "pose_landmarker_lite.task",
    "pose_landmarker_full.task",
    "pose_landmarker_heavy.task",
)
POSE_MODEL_PATHS = tuple(
    ROOT / "backend" / "perception" / name for name in POSE_MODEL_NAMES
)
BUNDLED_POSE_MODEL_PATHS = tuple(
    DIST_DIR
    / "Human Controller.app"
    / "Contents"
    / "Resources"
    / "backend"
    / "perception"
    / name
    for name in POSE_MODEL_NAMES
)
MEDIAPIPE_DIR_IN_BUNDLE = (
    DIST_DIR
    / "Human Controller.app"
    / "Contents"
    / "Frameworks"
    / "mediapipe"
)
MEDIAPIPE_NATIVE_LIBRARY_PATTERNS = (
    "tasks/c/libmediapipe.dylib",
    "python/_framework_bindings*.so",
)
APP_BUNDLE_PATH = DIST_DIR / "Human Controller.app"
PIP_HELPER_APP_PATH = (
    APP_BUNDLE_PATH
    / "Contents"
    / "Helpers"
    / "Human Controller PiP.app"
)
PIP_HELPER_EXECUTABLE_PATH = (
    PIP_HELPER_APP_PATH
    / "Contents"
    / "MacOS"
    / "Human Controller PiP"
)

# This helper is the "package the whole desktop app" script.
# It bundles the Qt app, built frontend files, and backend pose model into one
# macOS `.app` so teammates can test the real desktop experience.

SPEC_TEMPLATE = """# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

hiddenimports = collect_submodules("PySide6")
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("backend")
hiddenimports += collect_submodules("psutil")
mediapipe_binaries = collect_dynamic_libs("mediapipe")

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=mediapipe_binaries,
    datas=[
        ("frontend/dist", "frontend/dist"),
        ("backend/perception/pose_landmarker_lite.task", "backend/perception"),
        ("backend/perception/pose_landmarker_full.task", "backend/perception"),
        ("backend/perception/pose_landmarker_heavy.task", "backend/perception"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Human Controller",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Human Controller",
)

app = BUNDLE(
    coll,
    name="Human Controller.app",
    icon=None,
    bundle_identifier="au.edu.unsw.capstone.date.human-controller",
    info_plist={
        "CFBundleDisplayName": "Human Controller",
        "CFBundleName": "Human Controller",
        "NSCameraUsageDescription": "This app uses the camera to show the live session preview.",
        "NSPrincipalClass": "NSApplication",
        "NSHighResolutionCapable": True,
    },
)
"""


def create_pip_helper_bundle() -> bool:
    source_executable = (
        APP_BUNDLE_PATH / "Contents" / "MacOS" / "Human Controller"
    )
    helper_contents = PIP_HELPER_APP_PATH / "Contents"
    helper_macos = helper_contents / "MacOS"
    try:
        shutil.rmtree(PIP_HELPER_APP_PATH, ignore_errors=True)
        helper_macos.mkdir(parents=True)
        shutil.copy2(source_executable, PIP_HELPER_EXECUTABLE_PATH)
        os.symlink(
            "../../../Frameworks",
            helper_contents / "Frameworks",
            target_is_directory=True,
        )
        os.symlink(
            "../../../Resources",
            helper_contents / "Resources",
            target_is_directory=True,
        )
        with (helper_contents / "Info.plist").open("wb") as plist_file:
            plistlib.dump(
                {
                    "CFBundleDisplayName": "Human Controller PiP",
                    "CFBundleExecutable": "Human Controller PiP",
                    "CFBundleIdentifier": (
                        "au.edu.unsw.capstone.date.human-controller.pip"
                    ),
                    "CFBundleName": "Human Controller PiP",
                    "CFBundlePackageType": "APPL",
                    "CFBundleShortVersionString": "1.0",
                    "CFBundleVersion": "1",
                    "LSUIElement": True,
                    "NSHighResolutionCapable": True,
                    "NSPrincipalClass": "NSApplication",
                },
                plist_file,
            )
    except OSError as error:
        print(f"Failed to create PiP helper bundle: {error}")
        return False

    for bundle in (PIP_HELPER_APP_PATH, APP_BUNDLE_PATH):
        result = subprocess.run(
            ["codesign", "--force", "--sign", "-", str(bundle)],
            check=False,
        )
        if result.returncode != 0:
            print(f"Failed to sign app bundle: {bundle}")
            return False

    verification = subprocess.run(
        [
            "codesign",
            "--verify",
            "--deep",
            "--strict",
            str(APP_BUNDLE_PATH),
        ],
        check=False,
    )
    if verification.returncode != 0:
        print("Failed to verify the signed app bundle.")
        return False
    return True


def find_bundled_mediapipe_native_libraries() -> list[Path]:
    return sorted(
        {
            path
            for pattern in MEDIAPIPE_NATIVE_LIBRARY_PATTERNS
            for path in MEDIAPIPE_DIR_IN_BUNDLE.glob(pattern)
            if path.is_file()
        }
    )


def build_frontend() -> bool:
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if npm is None:
        print("Could not find npm. Install Node.js and ensure npm is on PATH.")
        return False

    print("Building frontend bundle for the packaged app...")
    result = subprocess.run([npm, "run", "build"], cwd=FRONTEND_DIR, check=False)
    return result.returncode == 0


def main() -> int:
    if sys.platform != "darwin":
        print("This builder is only intended for macOS.")
        return 1

    # The packaged app serves bundled frontend files, so we rebuild the UI here
    # to keep it aligned with the source shown by `make preview-local`.
    if not build_frontend():
        print("Frontend build failed; the macOS app bundle was not created.")
        return 1

    if not FRONTEND_PATH.exists():
        print("Frontend build finished without producing frontend/dist/index.html.")
        return 1

    # Pose estimation needs the MediaPipe task file at runtime. Packaging would
    # succeed without it, but the app would later fail when the camera flow starts.
    missing_models = [path for path in POSE_MODEL_PATHS if not path.exists()]
    if missing_models:
        for path in missing_models:
            print(f"Backend model asset is missing: {path}")
        return 1

    if shutil.which("pyinstaller") is None and not (ROOT / ".venv" / "bin" / "pyinstaller").exists():
        print("PyInstaller is not installed in the current environment.")
        print("Install it with: .venv/bin/python -m pip install pyinstaller")
        return 1

    # Force a fresh analysis whenever the desktop app grows new Python modules.
    # Relying on PyInstaller's cached analysis can leave recently added modules
    # out of the packaged app even after a successful rebuild.
    shutil.rmtree(ROOT / "build" / "human_controller", ignore_errors=True)
    shutil.rmtree(DIST_DIR / "Human Controller", ignore_errors=True)
    shutil.rmtree(DIST_DIR / "Human Controller.app", ignore_errors=True)

    SPEC_PATH.write_text(SPEC_TEMPLATE, encoding="utf-8")

    pyinstaller_executable = ROOT / ".venv" / "bin" / "pyinstaller"
    print("Building real macOS app bundle with integrated frontend and backend runtime...")
    if pyinstaller_executable.exists():
        command = [str(pyinstaller_executable), "--clean", "--noconfirm", str(SPEC_PATH)]
    else:
        command = ["pyinstaller", "--clean", "--noconfirm", str(SPEC_PATH)]

    PYINSTALLER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYINSTALLER_CONFIG_DIR"] = str(PYINSTALLER_CONFIG_DIR)

    result = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if result.returncode != 0:
        return result.returncode

    if not create_pip_helper_bundle():
        return 1

    if not find_bundled_mediapipe_native_libraries():
        expected_locations = ", ".join(
            str(MEDIAPIPE_DIR_IN_BUNDLE / pattern)
            for pattern in MEDIAPIPE_NATIVE_LIBRARY_PATTERNS
        )
        print(
            "Build failed validation: no supported MediaPipe native library "
            f"was bundled. Expected one of: {expected_locations}"
        )
        return 1

    missing_bundled_models = [
        path for path in BUNDLED_POSE_MODEL_PATHS if not path.exists()
    ]
    if missing_bundled_models:
        for path in missing_bundled_models:
            print(f"Build failed validation: pose model is missing: {path}")
        return 1

    print(f"Created macOS app bundle at: {APP_BUNDLE_PATH}")
    print('Launch it with: open "dist/Human Controller.app"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
