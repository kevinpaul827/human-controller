from PySide6.QtWidgets import QMenu, QStyle, QSystemTrayIcon

from .logging_utils import log_info


class MacOSMenuBar:
    def __init__(self, app, window, appkit=None):
        self.app = app
        self.window = window
        self.appkit = appkit
        self.tray_icon = None
        self.menu = None
        self.show_action = None
        self.hide_action = None
        self.quit_action = None

    def install(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log_info("[macos] menu bar status item is unavailable")
            return False

        self.menu = QMenu(self.window)
        self.show_action = self.menu.addAction("Show Main Window")
        self.hide_action = self.menu.addAction("Hide Main Window")
        self.menu.addSeparator()
        self.quit_action = self.menu.addAction("Quit Human Controller")

        self.show_action.triggered.connect(self.show_main_window)
        self.hide_action.triggered.connect(self.hide_main_window)
        self.quit_action.triggered.connect(self.quit_application)

        icon = self.app.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )
        self.tray_icon = QSystemTrayIcon(icon, self.window)
        self.tray_icon.setToolTip("Human Controller")
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()
        return True

    def show_main_window(self, _checked=False):
        if self.window.isMinimized():
            self.window.showNormal()
        else:
            self.window.show()
        self._activate_application()
        self.window.raise_()
        self.window.activateWindow()

    def hide_main_window(self, _checked=False):
        self.window.hide()

    def quit_application(self, _checked=False):
        self.app.quit()

    def shutdown(self):
        if self.tray_icon is not None:
            self.tray_icon.hide()

    def _activate_application(self):
        try:
            appkit = self.appkit
            if appkit is None:
                import AppKit as appkit_module

                appkit = appkit_module
            native_application = appkit.NSApplication.sharedApplication()
            activate = getattr(native_application, "activate", None)
            if callable(activate):
                activate()
                return
            activate_legacy = getattr(
                native_application,
                "activateIgnoringOtherApps_",
                None,
            )
            if callable(activate_legacy):
                activate_legacy(True)
        except Exception as error:
            log_info(f"[macos] failed to activate main window: {error!r}")
