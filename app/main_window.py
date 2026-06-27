import os

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

FRONTEND_PATH = "../frontend/dist/index.html"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Human Controller")
        self.resize(1200, 800)

        frontend = QWebEngineView()

        path = os.path.abspath(FRONTEND_PATH)
        frontend.setUrl(QUrl.fromLocalFile(path))

        self.setCentralWidget(frontend)
