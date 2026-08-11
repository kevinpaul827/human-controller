"""main.py

Creates the Qt application, opens the main window 
of the Human Controller app, then runs the app. It is
also responsible for checking app startup prerequisites.
"""
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .ui.main_window import (
    MainWindow,
    frontend_source_exists,
    frontend_source_for_display,
)


def main():
    """Initialize and run the Human Controller desktop application."""
    app = QApplication(sys.argv)

    # Desktop app only supports macOS and Windows.
    if sys.platform not in {"darwin", "win32"}:
        QMessageBox.critical(
            None,
            "Unsupported platform",
            "Human Controller supports only macOS and Windows.",
        )
        sys.exit(1)

    # Desktop app requires the frontend build.
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
        # Error if initilization of window fails.
        QMessageBox.critical(None, "Error", str(error))
        sys.exit(1)

    try:
        window.show()
        return app.exec()
    finally:
        # Ensure resources own by window are released
        window.shutdown()


if __name__ == "__main__":
    sys.exit(main())
