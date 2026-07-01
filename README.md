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

### Launching the Application

```bash
python3 -m app.main
```


## Checks

- `make app-check`: compiles and runs Python tests for `app/`.
- `make backend-check`: runs a compile check for `backend/`.

GitHub Actions currently enforce:

- `frontend-check.yml` for frontend lint, formatting, and type checks.
- `app-check.yml` for the Python app checks.
- `backend-check.yml` for backend dependency install and compile validation.
