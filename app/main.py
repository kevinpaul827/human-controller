import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .main_window import (
    MainWindow,
    frontend_source_exists,
    frontend_source_for_display,
)


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

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
