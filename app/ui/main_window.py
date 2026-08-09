import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

from ..bridges.calibration_bridge import CalibrateBridge
from ..bridges.profile_bridge import ProfileBridge
from ..bridges.session_bridge import SessionBridge
from ..bridges.state_bridge import StateBridge
from ..dev.backend_process import BackendProcessManager
from ..core.camera_manager import CameraManager
from ..gestures.gesture_store import GestureStore
from ..platforms.picture_in_picture import create_picture_in_picture
from ..profile_manager import ProfileManager
from ..utils.app_paths import user_data_dir
from .camera_overlay_widget import CameraOverlayWidget


def resolve_frontend_path():
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS"))
        return bundle_root / "frontend" / "dist" / "index.html"

    return (
        Path(__file__).resolve().parent.parent.parent
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
        self._shutdown_complete = False

        self.frontend = QWebEngineView()
        self.data_dir = user_data_dir()
        self.gesture_store = GestureStore(self.data_dir / "gestures")
        self.profile_manager = ProfileManager(self.data_dir / "profiles")
        self.camera_manager = CameraManager(self.gesture_store.gestures_dir)
        self.preview = CameraOverlayWidget(self.frontend)
        self.picture_in_picture = create_picture_in_picture()
        self.channel = QWebChannel()

        self._configure_preview_overlay()
        self._setup_state_bridge()
        self._setup_session_bridge()
        self._setup_calibration_bridge()
        self._setup_profile_bridge()
        self._maybe_autostart_backend()
        self._configure_frontend()

    def _configure_preview_overlay(self):
        self.preview.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        self.preview.setAutoFillBackground(True)
        self.preview.hide()

    def _setup_state_bridge(self):
        self.state_bridge = StateBridge(
            self.data_dir,
            self.gesture_store,
            self.profile_manager,
        )
        self.channel.registerObject("stateBridge", self.state_bridge)
        self.state_bridge.runtimeConfigurationChanged.connect(
            self.camera_manager.configure_runtime
        )
        self.camera_manager.configure_runtime(self.state_bridge.runtime_configuration())

    def _setup_session_bridge(self):
        self.session_bridge = SessionBridge(
            self.camera_manager,
            self.state_bridge,
        )
        self.channel.registerObject("sessionBridge", self.session_bridge)
        self.session_bridge.attach_picture_in_picture(self.picture_in_picture)

    def _setup_calibration_bridge(self):
        self.calibrate_bridge = CalibrateBridge(
            self.camera_manager,
            self.gesture_store,
        )
        self.channel.registerObject("calibrateBridge", self.calibrate_bridge)
        self.calibrate_bridge.attach_preview_widget(self.preview)
        self.calibrate_bridge.previewBoundsChanged.connect(
            self.handle_preview_bounds_changed
        )
        self.calibrate_bridge.poseEstimated.connect(self.preview.set_pose)

    def _setup_profile_bridge(self):
        self.profile_bridge = ProfileBridge(self.profile_manager, self.gesture_store)
        self.channel.registerObject("profileBridge", self.profile_bridge)
        self.profile_bridge.profilesChanged.connect(self.state_bridge.refreshProfiles)

    def _maybe_autostart_backend(self):
        if os.environ.get("HUMAN_CONTROLLER_BACKEND_AUTOSTART") != "1":
            return

        self.backend_manager = BackendProcessManager()
        self.backend_manager.start()

    def _configure_frontend(self):
        self.frontend.page().setWebChannel(self.channel)
        self.frontend.setUrl(frontend_qurl())
        self.setCentralWidget(self.frontend)

    def handle_preview_bounds_changed(self, left, top, width, height):
        self.preview.setGeometry(left, top, width, height)
        self.preview.raise_()

    def shutdown(self):
        if self._shutdown_complete:
            return
        self._shutdown_complete = True
        self.picture_in_picture.shutdown()
        self.camera_manager.shutdown()

        if self.backend_manager is not None:
            self.backend_manager.stop()

    def closeEvent(self, event):
        self.shutdown()
        QMainWindow.closeEvent(self, event)
