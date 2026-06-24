import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Human Controller")
        self.resize(1200, 800)

        frontend = QWebEngineView()

        path = os.path.abspath("../frontend/index.html")
        frontend.setUrl(QUrl.fromLocalFile(path))

        self.setCentralWidget(frontend)
