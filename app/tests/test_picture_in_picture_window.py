import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import app.picture_in_picture_window as picture_in_picture_module
from app.picture_in_picture_window import PictureInPictureWindow


class PictureInPictureWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        for window in QApplication.topLevelWidgets():
            if isinstance(window, PictureInPictureWindow):
                window.hide()
                window.deleteLater()
        self.application.processEvents()

    def test_macos_tool_window_attribute_is_set_before_show(self) -> None:
        with patch.object(picture_in_picture_module.sys, "platform", "darwin"):
            window = PictureInPictureWindow()

        self.assertFalse(window.isVisible())
        self.assertTrue(
            window.testAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        )

    def test_show_overlay_reasserts_native_configuration_after_show(self) -> None:
        with (
            patch.object(picture_in_picture_module.sys, "platform", "darwin"),
            patch.object(
                picture_in_picture_module,
                "configure_overlay_window",
                return_value=True,
            ) as configure,
            patch.object(picture_in_picture_module, "log_info") as log_info,
        ):
            window = PictureInPictureWindow()
            window.show_overlay()
            self.application.processEvents()

        self.assertEqual(configure.call_count, 2)
        configure.assert_called_with(window)
        log_info.assert_not_called()

    def test_deferred_configuration_can_recover_from_initial_failure(self) -> None:
        with (
            patch.object(picture_in_picture_module.sys, "platform", "darwin"),
            patch.object(
                picture_in_picture_module,
                "configure_overlay_window",
                side_effect=[False, True],
            ) as configure,
            patch.object(picture_in_picture_module, "log_info") as log_info,
        ):
            window = PictureInPictureWindow()
            window.show_overlay()
            self.application.processEvents()

        self.assertEqual(configure.call_count, 2)
        log_info.assert_not_called()

    def test_show_overlay_reports_native_configuration_failure(self) -> None:
        with (
            patch.object(picture_in_picture_module.sys, "platform", "darwin"),
            patch.object(
                picture_in_picture_module,
                "configure_overlay_window",
                return_value=False,
            ),
            patch.object(picture_in_picture_module, "log_info") as log_info,
        ):
            window = PictureInPictureWindow()
            window.show_overlay()
            self.application.processEvents()

        log_info.assert_called_once()
        self.assertIn(
            "native always-on-top configuration failed",
            log_info.call_args.args[0],
        )

    def test_deferred_configuration_does_not_reopen_hidden_overlay(self) -> None:
        with (
            patch.object(picture_in_picture_module.sys, "platform", "darwin"),
            patch.object(
                picture_in_picture_module,
                "configure_overlay_window",
                return_value=True,
            ) as configure,
        ):
            window = PictureInPictureWindow()
            window.show_overlay()
            window.hide_overlay()
            self.application.processEvents()

        self.assertFalse(window.isVisible())
        configure.assert_called_once_with(window)

    def test_close_event_does_not_dismiss_live_overlay(self) -> None:
        window = PictureInPictureWindow()
        window.show()
        event = MagicMock()

        window.closeEvent(event)

        event.ignore.assert_called_once()
        self.assertTrue(window.isVisible())
        self.assertFalse(hasattr(window, "close_button"))

if __name__ == "__main__":
    unittest.main()
