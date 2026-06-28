import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .main_window import MainWindow, FRONTEND_PATH

def main():
    app = QApplication(sys.argv)

    if not FRONTEND_PATH.exists():
        QMessageBox.critical(
            None,
            "Error",
            f"Could not find file {FRONTEND_PATH}\n"
            "Use command \"npm run build\" in frontend directory to setup frontend"
        )
            
        sys.exit(1)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
