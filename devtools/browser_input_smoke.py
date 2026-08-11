"""Browser input smoke tests"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.core.key_injector import KeyInjector


HTML = """
<!doctype html>
<html>
  <body tabindex="0">
    <h1>Human Controller browser input test</h1>
    <script>
      window.smoke = { events: [], framesWhileDown: 0, down: false };
      addEventListener("keydown", (event) => {
        window.smoke.events.push({
          type: event.type,
          key: event.key,
          code: event.code,
          keyCode: event.keyCode,
          trusted: event.isTrusted,
          repeat: event.repeat,
        });
        if (event.code === "KeyW") window.smoke.down = true;
      });
      addEventListener("keyup", (event) => {
        window.smoke.events.push({
          type: event.type,
          key: event.key,
          code: event.code,
          keyCode: event.keyCode,
          trusted: event.isTrusted,
          repeat: event.repeat,
        });
        if (event.code === "KeyW") window.smoke.down = false;
      });
      function sample() {
        if (window.smoke.down) window.smoke.framesWhileDown += 1;
        requestAnimationFrame(sample);
      }
      requestAnimationFrame(sample);
      document.body.focus();
    </script>
  </body>
</html>
"""


def run_browser_input_smoke(result_path: str) -> int:
    from PySide6.QtCore import QTimer
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = QWebEngineView()
    view.resize(640, 360)
    view.setWindowTitle("Human Controller Browser Input Test")
    injector = KeyInjector()
    output_path = Path(result_path)
    finished = {"value": False}

    def finish(result, exit_code):
        if finished["value"]:
            return
        finished["value"] = True
        output_path.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
        app.exit(exit_code)

    def report(raw_result):
        try:
            result = json.loads(raw_result)
        except (TypeError, json.JSONDecodeError):
            result = {"rawResult": raw_result, "events": [], "framesWhileDown": 0}
        events = result.get("events", []) if isinstance(result, dict) else []
        passed = (
            any(
                event.get("type") == "keydown" and event.get("code") == "KeyW"
                for event in events
            )
            and any(
                event.get("type") == "keyup" and event.get("code") == "KeyW"
                for event in events
            )
            and int(result.get("framesWhileDown", 0)) > 1
        )
        finish(result, 0 if passed else 1)

    def run_test(_ok=True):
        view.show()
        view.raise_()
        view.activateWindow()
        view.setFocus()
        QTimer.singleShot(750, lambda: injector.press("w"))
        QTimer.singleShot(1500, lambda: injector.release("w"))
        QTimer.singleShot(
            1800,
            lambda: view.page().runJavaScript(
                "JSON.stringify(window.smoke)",
                report,
            ),
        )

    view.loadFinished.connect(run_test)
    view.setHtml(HTML)
    QTimer.singleShot(
        5000,
        lambda: finish({"error": "smoke test timed out"}, 2),
    )
    return app.exec()
