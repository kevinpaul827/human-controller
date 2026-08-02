import re
import unittest
from pathlib import Path


SESSION_CAMERA_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "src"
    / "components"
    / "SessionCamera.tsx"
)


class FrontendSessionNavigationRegressionTests(unittest.TestCase):
    def test_unmounting_session_page_does_not_stop_live_session(self):
        source = SESSION_CAMERA_SOURCE.read_text(encoding="utf-8")
        stopping_cleanup = re.compile(
            r"return\s*\(\)\s*=>\s*\{[^{}]*"
            r"sessionBridge\.stopSession\s*\(",
            re.DOTALL,
        )

        self.assertIsNone(
            stopping_cleanup.search(source),
            "Session page unmount cleanup must not stop the desktop session",
        )


if __name__ == "__main__":
    unittest.main()
