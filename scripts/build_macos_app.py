import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
PYINSTALLER_CONFIG_DIR = ROOT / ".pyinstaller"
SPEC_PATH = ROOT / "human_controller.spec"
FRONTEND_PATH = ROOT / "frontend" / "dist" / "index.html"
POSE_MODEL_PATH = ROOT / "backend" / "perception" / "pose_landmarker_lite.task"

# This helper is the "package the whole desktop app" script.
# It bundles the Qt app, built frontend files, and backend pose model into one
# macOS `.app` so teammates can test the real desktop experience.

SPEC_TEMPLATE = """# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("PySide6")
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("backend")

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("frontend/dist", "frontend/dist"),
        ("backend/perception/pose_landmarker_lite.task", "backend/perception"),
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


def main() -> int:
    if sys.platform != "darwin":
        print("This builder is only intended for macOS.")
        return 1

    # The packaged app serves the built frontend files from inside the bundle,
    # so we fail early if the frontend has not been built yet.
    if not FRONTEND_PATH.exists():
        print("Frontend build is missing. Run `npm run build` in `frontend/` first.")
        return 1

    # Pose estimation needs the MediaPipe task file at runtime. Packaging would
    # succeed without it, but the app would later fail when the camera flow starts.
    if not POSE_MODEL_PATH.exists():
        print(f"Backend model asset is missing: {POSE_MODEL_PATH}")
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

    print(f"Created macOS app bundle at: {DIST_DIR / 'Human Controller.app'}")
    print('Launch it with: open "dist/Human Controller.app"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
