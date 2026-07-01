# App

This directory contains the Python files for creating the app of the project.

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

## Running the Application

```bash
python3 -m app.main
```

## Before Opening a PR

Please run the following checks locally before creating a pull request:

- `make app-check`: compiles and runs Python tests for `app/`.
