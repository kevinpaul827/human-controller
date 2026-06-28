from pathlib import Path
from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

FRONTEND_PATH = (
    Path(__file__).resolve().parent.parent
    / "frontend"
    / "dist"
    / "index.html"
)

class SessionBridge(QObject):
    sessionStatusChanged = Signal(dict)

    @Slot()
    def startSession(self):
        self.sessionStatusChanged.emit({"state": "starting"})
    
    @Slot()
    def stopSession(self):
        self.sessionStatusChanged.emit({"state": "idle"})

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Human Controller")
        self.resize(1200, 800)

        self.frontend = QWebEngineView()
        self.bridge = SessionBridge()
        self.channel = QWebChannel()
        self.channel.registerObject("sessionBridge", self.bridge)

        self.frontend.page().setWebChannel(self.channel)
        self.frontend.setUrl(QUrl.fromLocalFile(str(FRONTEND_PATH)))
        self.setCentralWidget(self.frontend)
