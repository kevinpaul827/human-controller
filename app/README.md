# App

This directory contains the Python files for creating the app of the project.

Repository build and packaging helpers live under `scripts/`, not in `app/`.

## Stack

- Python
- PySide6
- Pydantic (profile data validation)

## Structure

```text
├── app/
│   ├── main.py
│   ├── main_window.py
│   ├── session_bridge.py
│   ├── profile_demo.py
│   ├── profile_manager/
│   │   ├── manager.py
│   │   ├── models.py
│   │   └── exceptions.py
│   ├── data/profiles/
│   ├── requirements.txt
│   └── tests/
│       └── test_profile_manager.py
├── scripts/
│   ├── build_macos_app.py
│   └── sync_frontend_to_macos_app.py
```

## Profile Manager

Patient profiles are stored as versioned JSON files (`schemaVersion: 1`) under `app/data/profiles/`.

Each profile contains one or more game profiles; each game profile maps gesture names to keyboard keys and thresholds.

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
```

### Windows

```bash
python3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
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

These Make targets call the helper scripts in `scripts/`.

After the first packaged build:

- Frontend-only changes:

```bash
make macos-refresh-frontend
```

- Python desktop app changes:

```bash
make macos-app
```

## Running the Application

```bash
python3 -m app.main
```

## Camera permission notes

- macOS packaged builds must include `NSCameraUsageDescription` in the app bundle `Info.plist` for Qt camera permission requests to work.
- On Windows, camera access can still be blocked by `Settings > Privacy & security > Camera`, even if the app starts normally.

For local macOS testing, create and open the development app bundle:

```bash
make macos-app
open "dist/Human Controller.app"
```

If you only changed frontend files, you can update the packaged app faster with:

```bash
make macos-refresh-frontend
open "dist/Human Controller.app"
```

If you already denied access before, reset the camera permission first:

```bash
tccutil reset Camera
```

## Before Opening a PR

Please run the following checks locally before creating a pull request:

- `make app-check`: compiles and runs Python tests for `app/`.
