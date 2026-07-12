# capstone-project-26t2-3900-w18b-date

This repository is split into three main areas:

- `frontend/`: Vite + React + TypeScript web frontend.
- `app/`: Python desktop app code and tests.
- `backend/`: Early backend services and experiments, including camera input code in `camera_service/`.

## Current Structure

```text
.
├── app/
│   ├── main.py
│   ├── main_window.py
│   ├── session_bridge.py
│   ├── profile_manager/
│   ├── data/profiles/
│   ├── requirements.txt
│   └── tests/
├── backend/
│   ├── camera_service/
│   │   └── camera_feed.py
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
│   └── frontend-check.yml
└── Makefile
```

## Running the Application

Create a virtual environment and install the dependencies:

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

### Windows

```bash
python3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm ci
npm run build
```

## macOS Workflows

| Workflow | Command | Use it when | What it does | What updates quickly |
| --- | --- | --- | --- | --- |
| Packaged build | `make macos-app` | You changed desktop Python code, want a real app bundle, or need a packaged test build | Builds `Human Controller.app` with the desktop app, bundled frontend, backend helper runtime, and bundled backend assets | Nothing live; this is a rebuild step |
| Local preview | `make preview-local` | You want to iterate in the real desktop app while getting live frontend updates | Starts Vite, launches the desktop app in dev mode, and auto-starts a temporary backend helper | Frontend changes are prompt/live |
| Direct Python launch | `python3 -m app.main` | Non-macOS local runs or basic debugging without bundle-specific macOS behavior | Launches the desktop app directly from Python | No live frontend unless separately wired |

Notes:

- On macOS, run `make macos-app` once before `make preview-local` so camera permission works through the real app bundle identity.
- With `make preview-local`:
  - frontend changes: prompt/live
  - backend changes: auto-restart after save
  - desktop Python changes: still need `make macos-app` on macOS
- Optional preview logs:

```bash
make preview-local ARGS="--log-all"
make preview-local ARGS="--log-fe --log-be"
```

- If `preview-local` startup fails, it attempts to clean up leftover Human Controller, backend helper, and Vite processes before exiting.

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
