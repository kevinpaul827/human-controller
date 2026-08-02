import os
import unittest
from unittest.mock import call, patch

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
            patch.object(
                picture_in_picture_module,
                "set_overlay_activation_policy",
                return_value=True,
            ),
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
            patch.object(
                picture_in_picture_module,
                "set_overlay_activation_policy",
                return_value=True,
            ),
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
            patch.object(
                picture_in_picture_module,
                "set_overlay_activation_policy",
                return_value=True,
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
            patch.object(
                picture_in_picture_module,
                "set_overlay_activation_policy",
                return_value=True,
            ),
        ):
            window = PictureInPictureWindow()
            window.show_overlay()
            window.hide_overlay()
            self.application.processEvents()

        self.assertFalse(window.isVisible())
        configure.assert_called_once_with(window)

    def test_activation_policy_follows_overlay_visibility(self) -> None:
        with (
            patch.object(picture_in_picture_module.sys, "platform", "darwin"),
            patch.object(
                picture_in_picture_module,
                "configure_overlay_window",
                return_value=True,
            ),
            patch.object(
                picture_in_picture_module,
                "set_overlay_activation_policy",
                return_value=True,
            ) as set_policy,
        ):
            window = PictureInPictureWindow()
            window.show_overlay()
            self.application.processEvents()
            window.hide_overlay()

        self.assertEqual(set_policy.call_args_list, [call(True), call(False)])

    def test_shutdown_restores_regular_activation_policy(self) -> None:
        with patch.object(
            picture_in_picture_module,
            "set_overlay_activation_policy",
            return_value=True,
        ) as set_policy:
            window = PictureInPictureWindow()
            window.shutdown()

        set_policy.assert_called_once_with(False)

    def test_policy_transition_wraps_show_and_hide(self) -> None:
        events = []

        def record_policy(enabled):
            events.append(("policy", enabled))
            return True

        with (
            patch.object(picture_in_picture_module.sys, "platform", "darwin"),
            patch.object(
                picture_in_picture_module,
                "set_overlay_activation_policy",
                side_effect=record_policy,
            ),
            patch.object(
                picture_in_picture_module,
                "configure_overlay_window",
                side_effect=lambda _window: events.append(("configure", True))
                or True,
            ),
        ):
            window = PictureInPictureWindow()
            with patch.object(
                window,
                "show",
                side_effect=lambda: events.append(("show", True)),
            ):
                window.show_overlay()
            with patch.object(
                window,
                "hide",
                side_effect=lambda: events.append(("hide", True)),
            ):
                window.hide_overlay()

        self.assertEqual(
            events,
            [
                ("policy", True),
                ("show", True),
                ("configure", True),
                ("hide", True),
                ("policy", False),
            ],
        )

    def test_policy_failure_reports_fullscreen_limitation(self) -> None:
        with (
            patch.object(picture_in_picture_module.sys, "platform", "darwin"),
            patch.object(
                picture_in_picture_module,
                "set_overlay_activation_policy",
                return_value=False,
            ),
            patch.object(
                picture_in_picture_module,
                "configure_overlay_window",
                return_value=True,
            ),
            patch.object(picture_in_picture_module, "log_info") as log_info,
        ):
            window = PictureInPictureWindow()
            window.show_overlay()
            self.application.processEvents()

        log_info.assert_called_once()
        self.assertIn("accessory activation policy failed", log_info.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
