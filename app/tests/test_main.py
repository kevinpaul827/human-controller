import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
from unittest.mock import MagicMock, patch


_app_modules_before = {
    name: module
    for name, module in sys.modules.items()
    if name == "app" or name.startswith("app.")
}
_app_package = sys.modules.get("app")
_app_attributes_before = (
    dict(vars(_app_package)) if _app_package is not None else {}
)


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

_install_pose_processor_stub()
_install_overlay_constants_stub()
_install_picture_in_picture_stub()

from app import main
from app import main_window

for module_name in list(sys.modules):
    if (
        module_name == "app" or module_name.startswith("app.")
    ) and module_name not in _app_modules_before:
        sys.modules.pop(module_name, None)
for module_name, module in _app_modules_before.items():
    sys.modules[module_name] = module
if _app_package is not None:
    for attribute in list(vars(_app_package)):
        if attribute not in _app_attributes_before:
            delattr(_app_package, attribute)
    for attribute, value in _app_attributes_before.items():
        setattr(_app_package, attribute, value)


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
    @patch.object(main, "QApplication")
    @patch.object(main.QMessageBox, "critical")
    @patch.object(main.sys, "exit")
    def test_main_exits_with_error_when_frontend_is_missing(
        self,
        exit_mock,
        critical_mock,
        app_ctor_mock,
    ):
        exit_mock.side_effect = SystemExit(1)

        with patch.object(main, "frontend_source_exists", return_value=False):
            with patch.object(
                main,
                "frontend_source_for_display",
                return_value="/tmp/does-not-exist/index.html",
            ):
                with self.assertRaises(SystemExit):
                    main.main()

        app_ctor_mock.assert_called_once()
        critical_mock.assert_called_once()
        exit_mock.assert_called_once_with(1)

    @patch.object(main, "MainWindow", side_effect=RuntimeError("backend failed"))
    @patch.object(main, "QApplication")
    @patch.object(main.QMessageBox, "critical")
    @patch.object(main.sys, "exit")
    def test_main_exits_with_error_when_window_startup_fails(
        self,
        exit_mock,
        critical_mock,
        app_ctor_mock,
        _window_ctor_mock,
    ):
        exit_mock.side_effect = SystemExit(1)

        with patch.object(main.sys, "platform", "darwin"):
            with patch.object(main, "frontend_source_exists", return_value=True):
                with self.assertRaises(SystemExit):
                    main.main()

        app_ctor_mock.assert_called_once()
        critical_mock.assert_called_once()
        exit_mock.assert_called_once_with(1)

    @patch.object(main, "install_macos_menu_bar")
    @patch.object(main, "MainWindow")
    @patch.object(main, "QApplication")
    @patch.object(main.QMessageBox, "critical")
    @patch.object(main.sys, "exit")
    def test_main_starts_window_when_frontend_exists(
        self,
        exit_mock,
        critical_mock,
        app_ctor_mock,
        window_ctor_mock,
        install_menu_bar_mock,
    ):
        fake_app = MagicMock()
        fake_app.exec.return_value = 0
        fake_window = MagicMock()
        fake_menu_bar = MagicMock()
        app_ctor_mock.return_value = fake_app
        window_ctor_mock.return_value = fake_window
        install_menu_bar_mock.return_value = fake_menu_bar

        with patch.object(main.sys, "platform", "darwin"):
            with patch.object(main, "frontend_source_exists", return_value=True):
                self.assertEqual(main.main(), 0)

        critical_mock.assert_not_called()
        window_ctor_mock.assert_called_once()
        install_menu_bar_mock.assert_called_once_with(fake_app, fake_window)
        fake_window.show.assert_called_once()
        fake_app.exec.assert_called_once()
        fake_menu_bar.shutdown.assert_called_once()
        fake_window.shutdown.assert_called_once()
        exit_mock.assert_not_called()


class MacOSMenuBarInstallationTests(unittest.TestCase):
    @patch("app.macos_menu_bar.MacOSMenuBar")
    def test_successful_install_enables_close_to_hide(self, controller_class):
        app = MagicMock()
        window = MagicMock()
        controller = controller_class.return_value
        controller.install.return_value = True

        with patch.object(main.sys, "platform", "darwin"):
            self.assertIs(main.install_macos_menu_bar(app, window), controller)

        controller_class.assert_called_once_with(app, window)
        app.setQuitOnLastWindowClosed.assert_called_once_with(False)
        window.set_hide_on_close.assert_called_once_with(True)

    @patch("app.macos_menu_bar.MacOSMenuBar")
    def test_failed_install_keeps_normal_close_behavior(self, controller_class):
        app = MagicMock()
        window = MagicMock()
        controller_class.return_value.install.return_value = False

        with patch.object(main.sys, "platform", "darwin"):
            self.assertIsNone(main.install_macos_menu_bar(app, window))

        app.setQuitOnLastWindowClosed.assert_not_called()
        window.set_hide_on_close.assert_not_called()

    @patch.object(main, "log_info")
    @patch("app.macos_menu_bar.MacOSMenuBar", side_effect=RuntimeError("tray"))
    def test_install_error_keeps_normal_close_behavior(
        self,
        _controller_class,
        log_info,
    ):
        app = MagicMock()
        window = MagicMock()

        with patch.object(main.sys, "platform", "darwin"):
            self.assertIsNone(main.install_macos_menu_bar(app, window))

        app.setQuitOnLastWindowClosed.assert_not_called()
        window.set_hide_on_close.assert_not_called()
        log_info.assert_called_once()

    def test_non_macos_does_not_install_menu_bar(self):
        app = MagicMock()
        window = MagicMock()

        with patch.object(main.sys, "platform", "win32"):
            self.assertIsNone(main.install_macos_menu_bar(app, window))

        app.setQuitOnLastWindowClosed.assert_not_called()
        window.set_hide_on_close.assert_not_called()


class MainWindowCloseTests(unittest.TestCase):
    def test_close_hides_without_shutdown_when_menu_bar_is_installed(self):
        window = SimpleNamespace(
            _hide_on_close=True,
            hide=MagicMock(),
            shutdown=MagicMock(),
            picture_in_picture=MagicMock(),
        )
        window.picture_in_picture.isVisible.return_value = True
        event = MagicMock()

        main_window.MainWindow.closeEvent(window, event)

        window.hide.assert_called_once()
        event.ignore.assert_called_once()
        window.shutdown.assert_not_called()

    def test_close_quits_when_picture_in_picture_is_not_visible(self):
        window = SimpleNamespace(
            _hide_on_close=True,
            hide=MagicMock(),
            shutdown=MagicMock(),
            picture_in_picture=MagicMock(),
        )
        window.picture_in_picture.isVisible.return_value = False
        event = MagicMock()
        application = MagicMock()

        with (
            patch.object(
                main_window.QMainWindow,
                "closeEvent",
                create=True,
            ) as base_close,
            patch.object(
                main_window.QApplication,
                "instance",
                return_value=application,
                create=True,
            ),
        ):
            main_window.MainWindow.closeEvent(window, event)

        window.shutdown.assert_called_once()
        base_close.assert_called_once_with(window, event)
        application.quit.assert_called_once()

    def test_windows_close_preserves_normal_shutdown_path(self):
        window = SimpleNamespace(
            _hide_on_close=False,
            hide=MagicMock(),
            shutdown=MagicMock(),
            picture_in_picture=MagicMock(),
        )
        event = MagicMock()

        with patch.object(
            main_window.QMainWindow,
            "closeEvent",
            create=True,
        ) as base_close:
            main_window.MainWindow.closeEvent(window, event)

        window.shutdown.assert_called_once()
        base_close.assert_called_once_with(window, event)
