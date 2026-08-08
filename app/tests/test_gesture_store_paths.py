import os
import unittest
from pathlib import Path
from unittest.mock import patch

from app.gestures import gesture_store


class GestureStorePathResolutionTests(unittest.TestCase):
    def test_explicit_override_wins(self) -> None:
        with patch.dict(os.environ, {gesture_store.GESTURES_DIR_ENV: "/tmp/custom-gestures"}, clear=False):
            resolved = gesture_store.resolve_default_gestures_dir()

        self.assertEqual(resolved, Path("/tmp/custom-gestures").resolve())

    def test_project_root_is_used_for_dev(self) -> None:
        with patch.dict(
            os.environ,
            {
                gesture_store.PROJECT_ROOT_ENV: "/tmp/human-controller",
            },
            clear=False,
        ):
            resolved = gesture_store.resolve_default_gestures_dir()

        self.assertEqual(
            resolved,
            Path("/tmp/human-controller/app/data/gestures").resolve(),
        )

    def test_frozen_build_uses_user_app_support_dir(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(gesture_store.sys, "frozen", True, create=True):
                with patch.object(gesture_store.sys, "platform", "darwin"):
                    resolved = gesture_store.resolve_default_gestures_dir()

        self.assertEqual(
            resolved,
            Path.home() / "Library" / "Application Support" / "Human Controller" / "gestures",
        )


if __name__ == "__main__":
    unittest.main()
