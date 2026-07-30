import unittest
from pathlib import Path
from types import ModuleType
import sys
from unittest.mock import MagicMock, patch


def _install_pyside6_stub():
    for module_name in list(sys.modules):
        if module_name == "PySide6" or module_name.startswith("PySide6."):
            sys.modules.pop(module_name, None)

    pyside6_module = ModuleType("PySide6")
    qtcore_module = ModuleType("PySide6.QtCore")
    qtgui_module = ModuleType("PySide6.QtGui")
    qtmultimedia_module = ModuleType("PySide6.QtMultimedia")
    qtwebchannel_module = ModuleType("PySide6.QtWebChannel")
    qtwebengine_module = ModuleType("PySide6.QtWebEngineWidgets")
    qtmultimediawidgets_module = ModuleType("PySide6.QtMultimediaWidgets")
    qtwidgets_module = ModuleType("PySide6.QtWidgets")

    qtcore_module.Qt = type(
        "Qt",
        (),
        {
            "WidgetAttribute": type(
                "WidgetAttribute",
                (),
                {
                    "WA_TransparentForMouseEvents": object(),
                    "WA_TranslucentBackground": object(),
                },
            )
        },
    )
    qtcore_module.QLineF = type("QLineF", (), {})
    qtcore_module.QPointF = type("QPointF", (), {})
    qtcore_module.QRectF = type("QRectF", (), {})
    qtcore_module.QUrl = type(
        "QUrl",
        (),
        {
            "__init__": lambda self, value=None: None,
            "fromLocalFile": staticmethod(lambda path: path),
        },
    )
    qtcore_module.QCameraPermission = type("QCameraPermission", (), {})
    qtcore_module.QCoreApplication = type("QCoreApplication", (), {})
    qtcore_module.QElapsedTimer = type("QElapsedTimer", (), {})
    qtcore_module.QObject = type("QObject", (), {})
    qtcore_module.Signal = lambda *args, **kwargs: MagicMock()
    qtcore_module.Slot = lambda *args, **kwargs: (lambda func: func)
    qtcore_module.QThread = type("QThread", (), {})
    qtgui_module.QColor = type("QColor", (), {})
    qtgui_module.QDesktopServices = type("QDesktopServices", (), {})
    qtgui_module.QImage = type("QImage", (), {})
    qtgui_module.QPainter = type("QPainter", (), {})
    qtgui_module.QPen = type("QPen", (), {})
    qtmultimedia_module.QCamera = type("QCamera", (), {})
    qtmultimedia_module.QMediaCaptureSession = type("QMediaCaptureSession", (), {})
    qtmultimedia_module.QMediaDevices = type("QMediaDevices", (), {})
    qtmultimedia_module.QVideoFrame = type("QVideoFrame", (), {})
    qtmultimedia_module.QVideoSink = type("QVideoSink", (), {})
    qtwebchannel_module.QWebChannel = type("QWebChannel", (), {})
    qtwebengine_module.QWebEngineView = type("QWebEngineView", (), {})
    qtmultimediawidgets_module.QVideoWidget = type("QVideoWidget", (), {})
    qtwidgets_module.QApplication = type("QApplication", (), {})
    qtwidgets_module.QMessageBox = type(
        "QMessageBox",
        (),
        {"critical": staticmethod(lambda *args, **kwargs: None)},
    )
    qtwidgets_module.QMainWindow = type("QMainWindow", (), {})
    qtwidgets_module.QWidget = type("QWidget", (), {})

    sys.modules.setdefault("PySide6", pyside6_module)
    sys.modules["PySide6.QtCore"] = qtcore_module
    sys.modules["PySide6.QtGui"] = qtgui_module
    sys.modules["PySide6.QtMultimedia"] = qtmultimedia_module
    sys.modules["PySide6.QtWebChannel"] = qtwebchannel_module
    sys.modules["PySide6.QtWebEngineWidgets"] = qtwebengine_module
    sys.modules["PySide6.QtMultimediaWidgets"] = qtmultimediawidgets_module
    sys.modules["PySide6.QtWidgets"] = qtwidgets_module


def _install_pose_processor_stub():
    pose_processor_module = ModuleType("app.pose_processor")
    pose_processor_module.PoseProcessor = type("PoseProcessor", (), {})
    sys.modules["app.pose_processor"] = pose_processor_module


def _install_overlay_constants_stub():
    overlay_constants_module = ModuleType("app.overlay_constants")
    overlay_constants_module.MIN_VISIBILITY = 0.5
    overlay_constants_module.POSE_CONNECTIONS = []
    overlay_constants_module.connections_for_angle_joints = lambda _joints: set()
    overlay_constants_module.landmarks_for_angle_joints = lambda _joints: set()
    sys.modules["app.overlay_constants"] = overlay_constants_module


def _install_picture_in_picture_stub():
    picture_in_picture_module = ModuleType("app.picture_in_picture_window")
    picture_in_picture_module.PictureInPictureWindow = type(
        "PictureInPictureWindow", (), {}
    )
    sys.modules["app.picture_in_picture_window"] = picture_in_picture_module


try:
    from PySide6.QtCore import QElapsedTimer, QThread, Qt, QUrl  # noqa: F401
    from PySide6.QtGui import QDesktopServices, QImage  # noqa: F401
    from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices, QVideoFrame  # noqa: F401
    from PySide6.QtMultimediaWidgets import QVideoWidget  # noqa: F401
    from PySide6.QtWebChannel import QWebChannel  # noqa: F401
    from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
    from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox  # noqa: F401
except Exception:
    _install_pyside6_stub()

# These entrypoint tests only care about startup/error handling in app.main.
# Stubbing PoseProcessor keeps the import lightweight so the tests do not need
# numpy, OpenCV, or MediaPipe just to import the window module graph.
_install_pose_processor_stub()
_install_overlay_constants_stub()
_install_picture_in_picture_stub()

from app import main
from app import main_window

# Do not leak the lightweight import stub into overlay-specific test modules.
sys.modules.pop("app.overlay_constants", None)
sys.modules.pop("app.picture_in_picture_window", None)


class FrontendPathTests(unittest.TestCase):
    def test_frontend_path_targets_built_frontend_entrypoint(self):
        expected = (
            Path(__file__).resolve().parent.parent.parent
            / "frontend"
            / "dist"
            / "index.html"
        )

        self.assertEqual(main_window.FRONTEND_PATH, expected)

    def test_frontend_source_exists_with_dev_url(self):
        with patch.object(main_window, "FRONTEND_URL", "http://127.0.0.1:5173"):
            self.assertTrue(main_window.frontend_source_exists())


class MainEntryPointTests(unittest.TestCase):
    @patch("app.main.configure_macos_activation_policy")
    @patch("app.main.QApplication")
    @patch("app.main.QMessageBox.critical")
    @patch("app.main.sys.exit")
    def test_main_exits_with_error_when_frontend_is_missing(
        self,
        exit_mock,
        critical_mock,
        app_ctor_mock,
        activation_policy_mock,
    ):
        exit_mock.side_effect = SystemExit(1)

        with patch("app.main.frontend_source_exists", return_value=False):
            with patch(
                "app.main.frontend_source_for_display",
                return_value="/tmp/does-not-exist/index.html",
            ):
                with self.assertRaises(SystemExit):
                    main.main()

        app_ctor_mock.assert_called_once()
        activation_policy_mock.assert_called_once_with()
        critical_mock.assert_called_once()
        exit_mock.assert_called_once_with(1)

    @patch("app.main.configure_macos_activation_policy")
    @patch("app.main.MainWindow", side_effect=RuntimeError("backend failed"))
    @patch("app.main.QApplication")
    @patch("app.main.QMessageBox.critical")
    @patch("app.main.sys.exit")
    def test_main_exits_with_error_when_window_startup_fails(
        self,
        exit_mock,
        critical_mock,
        app_ctor_mock,
        _window_ctor_mock,
        activation_policy_mock,
    ):
        exit_mock.side_effect = SystemExit(1)

        with patch.object(main.sys, "platform", "darwin"):
            with patch("app.main.frontend_source_exists", return_value=True):
                with self.assertRaises(SystemExit):
                    main.main()

        app_ctor_mock.assert_called_once()
        activation_policy_mock.assert_called_once_with()
        critical_mock.assert_called_once()
        exit_mock.assert_called_once_with(1)

    @patch("app.main.configure_macos_activation_policy")
    @patch("app.main.MainWindow")
    @patch("app.main.QApplication")
    @patch("app.main.QMessageBox.critical")
    @patch("app.main.sys.exit")
    def test_main_starts_window_when_frontend_exists(
        self,
        exit_mock,
        critical_mock,
        app_ctor_mock,
        window_ctor_mock,
        activation_policy_mock,
    ):
        fake_app = MagicMock()
        fake_app.exec.return_value = 0
        fake_window = MagicMock()
        app_ctor_mock.return_value = fake_app
        window_ctor_mock.return_value = fake_window

        with patch.object(main.sys, "platform", "darwin"):
            with patch("app.main.frontend_source_exists", return_value=True):
                self.assertEqual(main.main(), 0)

        critical_mock.assert_not_called()
        activation_policy_mock.assert_called_once_with()
        window_ctor_mock.assert_called_once()
        fake_window.show.assert_called_once()
        fake_app.exec.assert_called_once()
        fake_window.shutdown.assert_called_once()
        exit_mock.assert_not_called()


class MacOSActivationPolicyTests(unittest.TestCase):
    def test_accessory_policy_is_applied_on_macos(self):
        appkit = MagicMock()
        appkit.NSApplicationActivationPolicyAccessory = 1
        native_application = appkit.NSApplication.sharedApplication.return_value
        native_application.setActivationPolicy_.return_value = True

        with patch.object(main.sys, "platform", "darwin"):
            self.assertTrue(main.configure_macos_activation_policy(appkit))

        native_application.setActivationPolicy_.assert_called_once_with(1)

    def test_activation_policy_is_unchanged_on_windows(self):
        appkit = MagicMock()

        with patch.object(main.sys, "platform", "win32"):
            self.assertFalse(main.configure_macos_activation_policy(appkit))

        appkit.NSApplication.sharedApplication.assert_not_called()

    def test_activation_policy_failure_is_visible(self):
        appkit = MagicMock()
        appkit.NSApplicationActivationPolicyAccessory = 1
        native_application = appkit.NSApplication.sharedApplication.return_value
        native_application.setActivationPolicy_.return_value = False

        with patch.object(main.sys, "platform", "darwin"):
            with patch("app.main.log_info") as log_mock:
                self.assertFalse(main.configure_macos_activation_policy(appkit))

        log_mock.assert_called_once_with(
            "[macos] accessory activation policy was rejected"
        )
