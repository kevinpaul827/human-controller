import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Human Controller")

        frontend = QWebEngineView()

        path = os.path.abspath("../frontend/index.html")
        frontend.setUrl(QUrl.fromLocalFile(path))

        self.setCentralWidget(frontend)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
