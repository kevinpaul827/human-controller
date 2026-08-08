# App

This folder contains the Python desktop application for Human Controller.

The desktop app is responsible for:

- creating the native Qt window
- loading the frontend inside `QWebEngineView`
- exposing Python bridge objects to the frontend through Qt WebChannel
- managing camera/session state
- optionally starting the local backend helper during preview mode

For full-project setup, use the root [README](../README.md). This file is the app-specific companion guide.

## Project Structure

- `main.py` — Desktop app entry point
- `ui/` — Qt windows, overlays, and frontend loading
- `bridges/` — Qt WebChannel bridge objects used by the frontend
- `core/` — Camera/session runtime orchestration
- `gestures/` — Gesture persistence and matching logic
- `profile_manager/` — Profile persistence, schema, and validation
- `platforms/` — OS-specific adapters for keyboard, windowing, and PiP behavior
- `calibration/` — Calibration capture flow
- `dev/` — Preview-only and development helpers
- `tools/` — Manual demos and utility entry points
- `utils/` — Shared app utilities
- `data/` — Saved profiles and gestures
- `tests/` — Desktop app tests

## How the Desktop App Fits In

The app sits between the React frontend and the Python backend code.

- `ui/main_window.py` loads either the built frontend files or a live Vite URL.
- `ui/main_window.py` registers `stateBridge`, `sessionBridge`, `calibrateBridge`, and `profileBridge` on a Qt `QWebChannel`.
- the frontend calls those bridge objects from TypeScript services
- the app manages the native calibration preview and Session picture-in-picture overlay
- in preview mode, `dev/backend_process.py` can start the local backend helper and wait for its `/health` endpoint

Important detail: camera pixels are not drawn by React. Calibration reports an
in-page viewport for the native Qt preview, while Session uses a separate
always-on-top picture-in-picture window.

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
python -m app.tools.profile_demo
```
