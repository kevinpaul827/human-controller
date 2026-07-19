"""Run the debug harness: ``python -m backend.debug_harness``."""

from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    # reload=False on purpose: this is a manual, throwaway debugging tool.
    uvicorn.run("backend.debug_harness.server:app", host="127.0.0.1", port=8000)
