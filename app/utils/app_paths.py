from __future__ import annotations

import os
import sys
from pathlib import Path

from app.product import APPLICATION_NAME as APP_DIR_NAME

DATA_DIR_ENV = "HUMAN_CONTROLLER_DATA_DIR"


def user_data_dir() -> Path:

    override = os.environ.get(DATA_DIR_ENV, "").strip()
    if override:
        path = Path(override).expanduser()
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    elif sys.platform == "win32":
        path = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_DIR_NAME
    else:
        raise RuntimeError("Human Controller supports only macOS and Windows.")
    path.mkdir(parents=True, exist_ok=True)
    return path
