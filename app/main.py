import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .logging_utils import log_info
from .main_window import (
    MainWindow,
    frontend_source_exists,
    frontend_source_for_display,
)


def configure_macos_activation_policy(appkit=None) -> bool:
    if sys.platform != "darwin":
        return False

    try:
        if appkit is None:
            import AppKit as appkit_module

            appkit = appkit_module

        native_application = appkit.NSApplication.sharedApplication()
        configured = bool(
            native_application.setActivationPolicy_(
                appkit.NSApplicationActivationPolicyAccessory
            )
        )
    except Exception as error:
        log_info(
            "[macos] failed to enable accessory activation policy: "
            f"{error!r}"
        )
        return False

    if not configured:
        log_info("[macos] accessory activation policy was rejected")
    return configured


def main():
    app = QApplication(sys.argv)
    configure_macos_activation_policy()

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

    window.show()

    try:
        return app.exec()
    finally:
        window.shutdown()


if __name__ == "__main__":
    sys.exit(main())
