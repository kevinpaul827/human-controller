# Human Controller

Human Controller is a desktop middleware application that enables patients to control existing games using rehabilitation exercises through gesture-to-keyboard mapping.

# GUI Installation (Windows)

- [**Windows download**](https://github.com/unsw-cse-comp99-3900/capstone-project-26t2-3900-w18b-date/releases/download/latest/Human-Controller-Windows.zip)
  
# GUI Installation (macOS)

You can download the macOS app here:
[**macOS download**](https://github.com/unsw-cse-comp99-3900/capstone-project-26t2-3900-w18b-date/releases/download/latest/Human-Controller-macOS.zip)

when you try to open the macOS app, you might get a pop up that looks like this:

<img width="260" height="248" alt="Screenshot 2026-08-11 at 10 03 37 pm" src="https://github.com/user-attachments/assets/349e51ff-8080-45b9-8b20-8c2eedddfd80" />

To resolve this, follow these instructions:

<img width="631" height="287" alt="Screenshot 2026-08-11 at 10 04 45 pm" src="https://github.com/user-attachments/assets/2f4b2a3c-610f-4c48-9b5e-ec8f90d09191" />

And click "Open Anyway"
<img width="464" height="108" alt="Screenshot 2026-08-11 at 10 05 06 pm" src="https://github.com/user-attachments/assets/67aafe21-decc-4bca-9a53-3f47bd048019" />


# Developer Instructions

This repo combines:

- a React frontend in `frontend/`
- a PySide6 desktop shell in `app/`
- Python backend and pose/matching code in `backend/`
- development helpers in `devtools/`

## Repo Layout

```text
.
├── app/        # Desktop app, Qt bridges, camera/session logic, tests
├── backend/    # Pose estimation and matching engine code
├── devtools/   # Preview helpers and development-only Python modules
├── frontend/   # React + TypeScript UI
├── scripts/    # Runnable wrappers for preview and packaging workflows
└── Makefile    # Common commands
```

## How the Parts Fit Together

At runtime, the React app is loaded inside a Qt `QWebEngineView`.

- `frontend/` renders the UI and calls Python bridge objects through Qt WebChannel.
- `app/` owns the native window, camera lifecycle, overlays, profile loading, and bridge objects such as `sessionBridge`, `calibrateBridge`, and `profileBridge`.
- `backend/` contains the pose and matching code used by the desktop flow.
- `devtools/` contains preview-only helpers such as the local health-check server and backend process manager.

In local preview mode:

- Vite serves the frontend at `http://127.0.0.1:5173`
- the desktop app loads that URL instead of built files
- the desktop app also auto-starts the local backend helper

Important detail: camera pixels are not drawn by React. Calibration reports an
in-page viewport for the native Qt preview, while Session uses a separate
always-on-top picture-in-picture window.

## Setup

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r app/requirements.txt
pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ..
```

Windows PowerShell:

```powershell
python3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r app/requirements.txt
pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ..
```

## Build the App

After following the setup instructions to finish the installation, you can build the desktop app:

macOS:

```bash
make macos-app
open "dist/Human Controller.app"
```

Windows Powershell:

```powershell
python -m PyInstaller run_app.spec --clean
dist/HumanController/"Human Controller".exe
```

`make macos-app` creates `dist/Human Controller.app`.

## Daily Development

Use this when you are actively working on the project and want the frontend, desktop app, and backend helper to run together:

```bash
make preview-local
```

This is the main integrated development workflow. It starts:

- the Vite dev server
- the desktop app
- the local backend helper

Frontend edits update live. Backend edits are auto-restarted by the preview script.

On Windows, if you do not use `make`:

```powershell
.\.venv\Scripts\python.exe scripts\preview_local.py
```

If you want more detail about the desktop shell itself, the Qt bridges, or app-specific notes, see [`app/README.md`](app/README.md).

### macOS Camera Note

On macOS, camera permission is tied to the real `.app` bundle identity.

If `make preview-local` cannot access the camera, build the app once first:

```bash
make macos-app
make preview-local
```

If camera access was previously denied:

```bash
tccutil reset Camera
```

### Checks

From the repo root:

```bash
make app-check
make backend-check
cd frontend && npm run lint
cd frontend && npm run typecheck
```

### Useful Commands

```bash
make preview-local   # full local preview flow
make macos-app       # build macOS desktop bundle
make app-check       # compile + test app/
make backend-check   # compile + test backend/
```
