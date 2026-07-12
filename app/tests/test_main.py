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
                {"WA_TransparentForMouseEvents": object()},
            )
        },
    )
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
    qtcore_module.QObject = type("QObject", (), {})
    qtcore_module.Signal = lambda *args, **kwargs: MagicMock()
    qtcore_module.Slot = lambda *args, **kwargs: (lambda func: func)
    qtgui_module.QDesktopServices = type("QDesktopServices", (), {})
    qtmultimedia_module.QCamera = type("QCamera", (), {})
    qtmultimedia_module.QMediaCaptureSession = type("QMediaCaptureSession", (), {})
    qtmultimedia_module.QMediaDevices = type("QMediaDevices", (), {})
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

    sys.modules.setdefault("PySide6", pyside6_module)
    sys.modules["PySide6.QtCore"] = qtcore_module
    sys.modules["PySide6.QtGui"] = qtgui_module
    sys.modules["PySide6.QtMultimedia"] = qtmultimedia_module
    sys.modules["PySide6.QtWebChannel"] = qtwebchannel_module
    sys.modules["PySide6.QtWebEngineWidgets"] = qtwebengine_module
    sys.modules["PySide6.QtMultimediaWidgets"] = qtmultimediawidgets_module
    sys.modules["PySide6.QtWidgets"] = qtwidgets_module


try:
    from PySide6.QtCore import Qt, QUrl  # noqa: F401
    from PySide6.QtGui import QDesktopServices  # noqa: F401
    from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices  # noqa: F401
    from PySide6.QtMultimediaWidgets import QVideoWidget  # noqa: F401
    from PySide6.QtWebChannel import QWebChannel  # noqa: F401
    from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
    from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox  # noqa: F401
except Exception:
    _install_pyside6_stub()

from app import main
from app import main_window


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
    @patch("app.main.QApplication")
    @patch("app.main.QMessageBox.critical")
    @patch("app.main.sys.exit")
    def test_main_exits_with_error_when_frontend_is_missing(
        self,
        exit_mock,
        critical_mock,
        app_ctor_mock,
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
        critical_mock.assert_called_once()
        exit_mock.assert_called_once_with(1)

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
    ):
        exit_mock.side_effect = SystemExit(1)

        with patch("app.main.frontend_source_exists", return_value=True):
            with self.assertRaises(SystemExit):
                main.main()

        app_ctor_mock.assert_called_once()
        critical_mock.assert_called_once()
        exit_mock.assert_called_once_with(1)

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
    ):
        fake_app = MagicMock()
        fake_app.exec.return_value = 0
        fake_window = MagicMock()
        app_ctor_mock.return_value = fake_app
        window_ctor_mock.return_value = fake_window
        exit_mock.side_effect = SystemExit(0)

        with patch("app.main.frontend_source_exists", return_value=True):
            with self.assertRaises(SystemExit):
                main.main()

        critical_mock.assert_not_called()
        window_ctor_mock.assert_called_once()
        fake_window.show.assert_called_once()
        fake_app.exec.assert_called_once()
        exit_mock.assert_called_once_with(0)
