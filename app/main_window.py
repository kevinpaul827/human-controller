import sys
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow
from PySide6.QtMultimediaWidgets import QVideoWidget

from .session_bridge import SessionBridge


def resolve_frontend_path():
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS"))
        return bundle_root / "frontend" / "dist" / "index.html"

    return (
        Path(__file__).resolve().parent.parent
        / "frontend"
        / "dist"
        / "index.html"
    )


FRONTEND_PATH = resolve_frontend_path()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Human Controller")
        self.resize(1200, 800)

        self.frontend = QWebEngineView()
        self.bridge = SessionBridge()
        self.preview = QVideoWidget(self.frontend)
        self.channel = QWebChannel()
        self.channel.registerObject("sessionBridge", self.bridge)

        self.preview.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.preview.setAutoFillBackground(True)
        self.preview.hide()

        self.bridge.attach_preview_widget(self.preview)
        self.bridge.previewBoundsChanged.connect(self.handle_preview_bounds_changed)

        self.frontend.page().setWebChannel(self.channel)
        self.frontend.setUrl(QUrl.fromLocalFile(str(FRONTEND_PATH)))
        self.setCentralWidget(self.frontend)

    def handle_preview_bounds_changed(self, left, top, width, height):
        self.preview.setGeometry(left, top, width, height)
        self.preview.raise_()
