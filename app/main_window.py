from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

FRONTEND_PATH = (
    Path(__file__).resolve().parent.parent
    / "frontend"
    / "dist"
    / "index.html"
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Human Controller")
        self.resize(1200, 800)

        frontend = QWebEngineView()
        frontend.setUrl(QUrl.fromLocalFile(str(FRONTEND_PATH)))

        self.setCentralWidget(frontend)
