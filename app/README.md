# App

This folder contains the Python desktop application for Human Controller.

The desktop app is responsible for:

- creating the native Qt window
- loading the frontend inside `QWebEngineView`
- exposing Python bridge objects to the frontend through Qt WebChannel
- managing camera/session state
- optionally starting the local backend helper during preview mode

For full-project setup, use the root [README](../README.md). This file is the app-specific companion guide.

## Key Files

```text
app/
├── main.py                  # App entry point
├── main_window.py           # Main Qt window and frontend loading
├── session_bridge.py        # Session page bridge between React and Python
├── calibrate_bridge.py      # Calibration bridge
├── profile_bridge.py        # Profile management bridge
├── camera_overlay_widget.py # Native camera/pose overlay
├── camera_manager.py        # Camera lifecycle and frame processing
├── backend_process.py       # Starts/stops the local backend helper
├── pose_processor.py        # Pose processing pipeline
├── profile_manager/         # Profile loading, validation, persistence
├── data/profiles/           # Saved patient profiles
├── data/gestures/           # Saved gesture definitions
└── tests/                   # Desktop app tests
```

## How the Desktop App Fits In

The app sits between the React frontend and the Python backend code.

- `main_window.py` loads either the built frontend files or a live Vite URL.
- `main_window.py` registers `sessionBridge`, `calibrateBridge`, and `profileBridge` on a Qt `QWebChannel`.
- the frontend calls those bridge objects from TypeScript services
- the app manages the native preview overlay so the camera feed stays aligned with the session page
- in preview mode, `backend_process.py` can start the local backend helper and wait for its `/health` endpoint

Important detail: the session camera preview is not drawn by React. The frontend reports where the preview should appear, and the desktop app overlays the native Qt camera widget on top of the web page.

## Run the App

From the repo root, after following the root setup instructions:

```bash
python3 -m app.main
```

This expects the frontend build to already exist in `frontend/dist`.

If you want the main integrated development workflow instead, use:

```bash
make preview-local
```

That preview workflow starts:

- the Vite dev server
- the desktop app
- the local backend helper

## App-Specific Notes

### Frontend requirement

If `frontend/dist/index.html` is missing, the desktop app will not start and will ask you to run the frontend build first.

### macOS camera permission

On macOS, camera permission works best when the app is launched as the packaged `.app` bundle:

```bash
make macos-app
open "dist/Human Controller.app"
```

For local preview on macOS, you may need to build the app bundle once before running:

```bash
make macos-app
make preview-local
```

This matches the project-level macOS note in the root README.

### Logging

The preview flow supports desktop log levels through `HUMAN_CONTROLLER_LOG_LEVEL`:

```bash
HUMAN_CONTROLLER_LOG_LEVEL=info make preview-local
HUMAN_CONTROLLER_LOG_LEVEL=debug make preview-local
HUMAN_CONTROLLER_LOG_LEVEL=verbose make preview-local
HUMAN_CONTROLLER_LOG_LEVEL=silent make preview-local
```

## Tests

Run the app checks from the repo root:

```bash
make app-check
```

Run a single test module if needed:

```bash
python -m unittest app.tests.test_profile_manager -v
```

## Demo

To run the profile demo:

```bash
python -m app.profile_demo
```
