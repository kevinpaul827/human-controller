

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dev.browser_input_smoke import run_browser_input_smoke


if __name__ == "__main__":
    result_path = Path(tempfile.gettempdir()) / "human-controller-input-smoke.json"
    exit_code = run_browser_input_smoke(str(result_path))
    if result_path.exists():
        print(result_path.read_text(encoding="utf-8"))
    raise SystemExit(exit_code)
