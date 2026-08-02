import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .logging_utils import log_info
from .main_window import (
    MainWindow,
    frontend_source_exists,
    frontend_source_for_display,
)


def install_macos_menu_bar(app, window):
    if sys.platform != "darwin":
        return None

    from .macos_menu_bar import MacOSMenuBar

    try:
        menu_bar = MacOSMenuBar(app, window)
        installed = menu_bar.install()
    except Exception as error:
        log_info(f"[macos] failed to install menu bar: {error!r}")
        return None

    if not installed:
        return None

    app.setQuitOnLastWindowClosed(False)
    window.set_hide_on_close(True)
    return menu_bar


def main():
    app = QApplication(sys.argv)

    if sys.platform not in {"darwin", "win32"}:
        QMessageBox.critical(
            None,
            "Unsupported platform",
            "Human Controller supports only macOS and Windows.",
        )
        sys.exit(1)

    if not frontend_source_exists():
        QMessageBox.critical(
            None,
            "Error",
            f"Could not find frontend source {frontend_source_for_display()}\n"
            'Use command "npm run build" in frontend directory to setup frontend',
        )

        sys.exit(1)

    try:
        window = MainWindow()
    except RuntimeError as error:
        QMessageBox.critical(None, "Error", str(error))
        sys.exit(1)

    menu_bar = None
    try:
        menu_bar = install_macos_menu_bar(app, window)
        window.show()
        return app.exec()
    finally:
        if menu_bar is not None:
            menu_bar.shutdown()
        window.shutdown()


if __name__ == "__main__":
    sys.exit(main())
