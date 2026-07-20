import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

from .backend_process import BackendProcessManager
from .calibrate_bridge import CalibrateBridge
from .camera_manager import CameraManager
from .camera_overlay_widget import CameraOverlayWidget
from .profile_bridge import ProfileBridge
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


def resolve_frontend_url():
    frontend_url = os.environ.get("HUMAN_CONTROLLER_FRONTEND_URL", "").strip()
    return frontend_url or None


FRONTEND_PATH = resolve_frontend_path()
FRONTEND_URL = resolve_frontend_url()


def frontend_source_exists():
    return FRONTEND_URL is not None or FRONTEND_PATH.exists()


def frontend_source_for_display():
    return FRONTEND_URL or str(FRONTEND_PATH)


def frontend_qurl():
    if FRONTEND_URL:
        return QUrl(FRONTEND_URL)

    return QUrl.fromLocalFile(str(FRONTEND_PATH))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Human Controller")
        self.resize(1200, 800)
        self.backend_manager = None

        self.frontend = QWebEngineView()
        self.camera_manager = CameraManager()
        self.preview = CameraOverlayWidget(self.frontend)
        self.channel = QWebChannel()

        self.preview.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.preview.setAutoFillBackground(True)
        self.preview.hide()

        self.session_bridge = SessionBridge(self.camera_manager)
        self.channel.registerObject("sessionBridge", self.session_bridge)
        self.session_bridge.attach_preview_widget(self.preview)
        self.session_bridge.previewBoundsChanged.connect(self.handle_preview_bounds_changed)
        self.session_bridge.poseEstimated.connect(self.preview.set_pose)
    
        self.calibrate_bridge = CalibrateBridge(self.camera_manager)
        self.channel.registerObject("calibrateBridge", self.calibrate_bridge)
        self.calibrate_bridge.attach_preview_widget(self.preview)
        self.calibrate_bridge.previewBoundsChanged.connect(self.handle_preview_bounds_changed)
        self.calibrate_bridge.poseEstimated.connect(self.preview.set_pose)

        self.profile_bridge = ProfileBridge()
        self.channel.registerObject("profileBridge", self.profile_bridge)

        if os.environ.get("HUMAN_CONTROLLER_BACKEND_AUTOSTART") == "1":
            self.backend_manager = BackendProcessManager()
            self.backend_manager.start()

        self.frontend.page().setWebChannel(self.channel)
        self.frontend.setUrl(frontend_qurl())
        self.setCentralWidget(self.frontend)

    def handle_preview_bounds_changed(self, left, top, width, height):
        self.preview.setGeometry(left, top, width, height)
        self.preview.raise_()

    def closeEvent(self, event):
        self.camera_manager.shutdown()

        if self.backend_manager is not None:
            self.backend_manager.stop()
        super().closeEvent(event)
