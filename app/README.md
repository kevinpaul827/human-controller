# App

This directory contains the Python desktop app code for the project.

Repository build and packaging helpers live under `scripts/`, not in `app/`.

## Stack

- Python
- PySide6
- Pydantic (profile data validation)
- NumPy and OpenCV (camera frame processing for pose estimation)

## Structure

```text
├── app/
│   ├── backend_process.py
│   ├── camera_overlay_widget.py
│   ├── logging_utils.py
│   ├── main.py
│   ├── main_window.py
│   ├── pose_processor.py
│   ├── session_bridge.py
│   ├── profile_demo.py
│   ├── profile_manager/
│   │   ├── manager.py
│   │   ├── models.py
│   │   └── exceptions.py
│   ├── data/profiles/
│   ├── requirements.txt
│   ├── tests/
│       ├── test_backend_process.py
│       ├── test_main.py
│       └── test_profile_manager.py
│   └── unused/
│       └── camera_reader.py
├── backend/
│   ├── dev_server.py
│   └── perception/
├── scripts/
│   ├── build_macos_app.py
│   ├── preview_local.py
│   └── run_backend_dev.py
```

Plain English:
- `main.py` is the app entry point.
- `main_window.py` builds the main Qt window and loads the frontend.
- `session_bridge.py` is the bridge between the web frontend and the Qt/camera side.
- `camera_overlay_widget.py` draws the native desktop session preview and pose overlay.
- `pose_processor.py` turns Qt camera frames into data the backend pose estimator can use on a worker thread.
- `logging_utils.py` provides simple `info` / `debug` / `verbose` log gating for the desktop app.
- `backend_process.py` starts and stops the small backend helper used in preview and packaged builds.
- `scripts/` contains developer tooling such as packaging and local preview helpers.

## Profile Manager

Patient profiles are stored as versioned JSON files (`schemaVersion: 2`) under
`app/data/profiles/`.

Each profile stores a `keyBindings` map from calibrated `gesture_id` values to
keyboard keys. Gesture recognition data remains separate under
`app/data/gestures/`.

### Run tests

```bash
python -m unittest app.tests.test_profile_manager -v
```

### Run demo

```bash
python -m app.profile_demo
```

## Setup

Create a virtual environment and install the dependencies:

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
pip install -r backend/requirements.txt
pip install -r backend/matching_engine/requirements.txt
```

### Windows

```bash
python3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
pip install -r backend/requirements.txt
pip install -r backend/matching_engine/requirements.txt
```

## Frontend Setup

```bash
cd frontend
npm ci
npm run build
```

For macOS packaged-app development:

```bash
make macos-app
```

The packaged app build is intended to include the desktop app, built frontend,
and backend helper runtime in one macOS artifact.

`make macos-app` now performs a clean PyInstaller rebuild, so newly added
desktop modules are picked up without needing manual cache cleanup.

After the first packaged build, rebuild the packaged app whenever frontend or
Python desktop app changes:

```bash
make macos-app
```

## Running the Application

```bash
python3 -m app.main
```

For integrated local preview during development:

```bash
make macos-app
make preview-local
```

On Windows, GNU Make is optional; run the cross-platform supervisor directly:

```powershell
.\.venv\Scripts\python.exe scripts\preview_local.py
```

This loads the frontend from the Vite dev server and starts a temporary backend
helper process under the desktop app.

Desktop session preview behavior:
- the React session page reports the preview viewport bounds to Qt
- the desktop app positions a native overlay widget over that viewport
- the overlay now renders the frame that was actually used for pose inference,
  so the displayed image and landmarks stay synchronized

The preview helper is mainly for development convenience:
- frontend code updates live from Vite
- backend helper code restarts automatically
- desktop Python code inside the packaged macOS app still needs `make macos-app` again

Desktop logging can be tuned with `HUMAN_CONTROLLER_LOG_LEVEL`:

```bash
HUMAN_CONTROLLER_LOG_LEVEL=info make preview-local
HUMAN_CONTROLLER_LOG_LEVEL=debug make preview-local
HUMAN_CONTROLLER_LOG_LEVEL=verbose make preview-local
HUMAN_CONTROLLER_LOG_LEVEL=silent make preview-local
```

On macOS, the initial `make macos-app` step is required so the app runs with the
bundle identity needed for camera permissions.

## Camera permission notes

- macOS packaged builds must include `NSCameraUsageDescription` in the app bundle `Info.plist` for Qt camera permission requests to work.
- On Windows, camera access can still be blocked by `Settings > Privacy & security > Camera`, even if the app starts normally.

For local macOS testing, create and open the development app bundle:

```bash
make macos-app
open "dist/Human Controller.app"
```

If you changed frontend assets, rebuild the packaged app before testing it:

```bash
make macos-app
open "dist/Human Controller.app"
```

If you already denied access before, reset the camera permission first:

```bash
tccutil reset Camera
```

## Before Opening a PR

Please run the following checks locally before creating a pull request:

- `make app-check`: compiles and runs Python tests for `app/`.
