from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def json_path(directory: Path, identifier: str, *, label: str) -> Path:
    """Return a JSON path for a safe, single-file identifier.

    Identifiers are deliberately narrower than general filenames because they
    cross the Qt bridge and may ultimately originate in browser input.
    """
    resolved_identifier = str(identifier or "").strip()
    if not _SAFE_IDENTIFIER.fullmatch(resolved_identifier):
        raise ValueError(
            f"{label} must be 1-64 letters, numbers, dots, dashes, or underscores."
        )
    if resolved_identifier in {".", ".."}:
        raise ValueError(f"{label} must not contain a path.")
    return Path(directory) / f"{resolved_identifier}.json"


def write_json_atomic(path: Path, payload: Any) -> None:
    """Write JSON without exposing a partially-written destination file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(payload, temporary, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        temporary_path.replace(destination)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
