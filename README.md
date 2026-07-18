# capstone-project-26t2-3900-w18b-date

This repository is split into three main areas:

- `frontend/`: Vite + React + TypeScript web frontend.
- `app/`: Python desktop app, Qt session bridge, backend launcher, and tests.
- `backend/`: Pose-estimation and development backend helpers used by the desktop app.

## Current Structure

```text
.
├── app/
│   ├── backend_process.py
│   ├── camera_overlay_widget.py
│   ├── logging_utils.py
│   ├── main.py
│   ├── main_window.py
│   ├── pose_processor.py
│   ├── session_bridge.py
│   ├── profile_manager/
│   ├── data/profiles/
│   ├── requirements.txt
│   └── tests/
├── backend/
│   ├── camera_service/
│   │   └── camera_feed.py
│   ├── dev_server.py
│   ├── matching_engine/
│   ├── perception/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── .github/workflows/
│   ├── app-check.yml
│   ├── backend-check.yml
│   ├── frontend-check.yml
│   └── macos-app-build.yml
├── scripts/
│   ├── build_macos_app.py
│   ├── preview_local.py
│   └── run_backend_dev.py
└── Makefile
```

## Running the Application

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

### Frontend Setup

```bash
cd frontend
npm ci
npm run build
```

## Development Workflows

| Workflow | Command | Use it when | What it does | What updates quickly |
| --- | --- | --- | --- | --- |
| Packaged build | `make macos-app` | You changed desktop Python code, want a real app bundle, or need a packaged test build | Builds `Human Controller.app` with the desktop app, bundled frontend, backend helper runtime, and bundled backend assets | Nothing live; this is a rebuild step |
| Local preview | `make preview-local` | You want to iterate in the real desktop app while getting live frontend updates | Starts Vite, launches the desktop app in dev mode, and auto-starts a temporary backend helper | Frontend changes are prompt/live |
| Direct Python launch | `python3 -m app.main` | Non-macOS local runs or basic debugging without bundle-specific macOS behavior | Launches the desktop app directly from Python | No live frontend unless separately wired |

Plain English:
- `make macos-app` is the packaging/build workflow.
- `make preview-local` is the easiest day-to-day development workflow when you want the desktop app and web UI running together.
- The `scripts/` folder contains helper tools for packaging and preview; it is not app runtime code by itself.
- The desktop session preview is rendered by a native Qt overlay widget that stays aligned with the React session page.

On Windows, GNU Make is optional. Run the equivalent workflow from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\preview_local.py
```

Optional logging uses the same flags as the Make target:

```powershell
.\.venv\Scripts\python.exe scripts\preview_local.py --log-fe --log-be
```

Notes:

- On macOS, run `make macos-app` once before `make preview-local` so camera permission works through the real app bundle identity.
- `make macos-app` performs a clean PyInstaller rebuild and refreshes the packaged app bundle from the current source tree.
- `make preview-local` also expects the backend Python dependencies above to be installed, because it auto-starts the preview backend helper.
- With `make preview-local`:
  - frontend changes: prompt/live
  - backend changes: auto-restart after save
  - desktop Python changes: still need `make macos-app` on macOS
- Optional preview logs:

```bash
make preview-local ARGS="--log-all"
make preview-local ARGS="--log-fe --log-be"
```

- Desktop app log verbosity can also be controlled with `HUMAN_CONTROLLER_LOG_LEVEL`:

```bash
HUMAN_CONTROLLER_LOG_LEVEL=info make preview-local
HUMAN_CONTROLLER_LOG_LEVEL=debug make preview-local
HUMAN_CONTROLLER_LOG_LEVEL=verbose make preview-local
```

- If `preview-local` startup fails, it attempts to clean up the frontend, desktop app, and their child processes before exiting.

### macOS Camera Permission Fix

If macOS denies camera access, launch the desktop app as a real `.app` bundle so it can provide `NSCameraUsageDescription`:

```bash
make macos-app
open "dist/Human Controller.app"
```

If you changed frontend assets, rebuild the packaged app before testing the bundle:

```bash
make macos-app
open "dist/Human Controller.app"
```

If you changed desktop Python modules on macOS, rebuild the packaged app before running `make preview-local` again:

```bash
make macos-app
make preview-local
```

If you already denied access earlier, reset camera permission and relaunch:

```bash
tccutil reset Camera
```


## Checks

- `make app-check`: compiles and runs Python tests for `app/`.
- `make backend-check`: runs a compile check for `backend/`.

GitHub Actions currently enforce:

- `frontend-check.yml` for frontend lint, formatting, and type checks.
- `app-check.yml` for the Python app checks.
- `backend-check.yml` for backend dependency install and compile validation.
- `macos-app-build.yml` for packaged macOS app build and downloadable artifact upload.
