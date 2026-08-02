import unittest
from unittest.mock import MagicMock, patch

import app.macos_menu_bar as menu_bar_module
from app.macos_menu_bar import MacOSMenuBar


class FakeSignal:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)

    def emit(self, value=False):
        for slot in self.slots:
            slot(value)


class FakeAction:
    def __init__(self, text):
        self.text = text
        self.triggered = FakeSignal()


class FakeMenu:
    def __init__(self, parent):
        self.parent = parent
        self.entries = []

    def addAction(self, text):
        action = FakeAction(text)
        self.entries.append(action)
        return action

    def addSeparator(self):
        self.entries.append(None)


class FakeTrayIcon:
    available = True

    @classmethod
    def isSystemTrayAvailable(cls):
        return cls.available

    def __init__(self, icon, parent):
        self.icon = icon
        self.parent = parent
        self.tooltip = None
        self.menu = None
        self.visible = False

    def setToolTip(self, tooltip):
        self.tooltip = tooltip

    def setContextMenu(self, menu):
        self.menu = menu

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False


class MacOSMenuBarTests(unittest.TestCase):
    def setUp(self):
        self.app = MagicMock()
        self.icon = object()
        self.app.style.return_value.standardIcon.return_value = self.icon
        self.window = MagicMock()
        self.window.isMinimized.return_value = False
        self.appkit = MagicMock()
        self.native_application = (
            self.appkit.NSApplication.sharedApplication.return_value
        )

    def install_menu_bar(self):
        controller = MacOSMenuBar(self.app, self.window, self.appkit)
        with (
            patch.object(menu_bar_module, "QMenu", FakeMenu),
            patch.object(menu_bar_module, "QSystemTrayIcon", FakeTrayIcon),
        ):
            installed = controller.install()
        self.assertTrue(installed)
        return controller

    def test_install_adds_show_hide_and_quit_actions(self):
        controller = self.install_menu_bar()

        self.assertEqual(
            [
                entry.text if entry is not None else None
                for entry in controller.menu.entries
            ],
            [
                "Show Main Window",
                "Hide Main Window",
                None,
                "Quit Human Controller",
            ],
        )
        self.assertIs(controller.tray_icon.icon, self.icon)
        self.assertEqual(controller.tray_icon.tooltip, "Human Controller")
        self.assertIs(controller.tray_icon.menu, controller.menu)
        self.assertTrue(controller.tray_icon.visible)

    def test_show_action_restores_and_activates_main_window(self):
        controller = self.install_menu_bar()

        controller.show_action.triggered.emit(True)

        self.window.show.assert_called_once()
        self.window.showNormal.assert_not_called()
        self.native_application.activate.assert_called_once()
        self.window.raise_.assert_called_once()
        self.window.activateWindow.assert_called_once()

    def test_show_action_restores_a_minimized_window(self):
        self.window.isMinimized.return_value = True
        controller = self.install_menu_bar()

        controller.show_action.triggered.emit(True)

        self.window.showNormal.assert_called_once()
        self.window.show.assert_not_called()

    def test_hide_action_only_hides_main_window(self):
        controller = self.install_menu_bar()

        controller.hide_action.triggered.emit(True)

        self.window.hide.assert_called_once()
        self.window.shutdown.assert_not_called()

    def test_quit_action_exits_application(self):
        controller = self.install_menu_bar()

        controller.quit_action.triggered.emit(True)

        self.app.quit.assert_called_once()
        self.window.close.assert_not_called()

    def test_shutdown_hides_status_item(self):
        controller = self.install_menu_bar()

        controller.shutdown()

        self.assertFalse(controller.tray_icon.visible)

    @patch.object(menu_bar_module, "log_info")
    def test_install_fails_when_status_items_are_unavailable(self, log_info):
        unavailable_tray = type(
            "UnavailableTray",
            (FakeTrayIcon,),
            {"available": False},
        )
        controller = MacOSMenuBar(self.app, self.window, self.appkit)

        with patch.object(
            menu_bar_module,
            "QSystemTrayIcon",
            unavailable_tray,
        ):
            self.assertFalse(controller.install())

        self.assertIsNone(controller.tray_icon)
        log_info.assert_called_once_with(
            "[macos] menu bar status item is unavailable"
        )


if __name__ == "__main__":
    unittest.main()
