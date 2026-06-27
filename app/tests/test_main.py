import unittest
from pathlib import Path
from types import ModuleType
import sys
from unittest.mock import MagicMock, patch


def _install_pyside6_stub():
    pyside6_module = ModuleType("PySide6")
    qtcore_module = ModuleType("PySide6.QtCore")
    qtwebengine_module = ModuleType("PySide6.QtWebEngineWidgets")
    qtwidgets_module = ModuleType("PySide6.QtWidgets")

    qtcore_module.QUrl = type(
        "QUrl",
        (),
        {"fromLocalFile": staticmethod(lambda path: path)},
    )
    qtwebengine_module.QWebEngineView = type("QWebEngineView", (), {})
    qtwidgets_module.QApplication = type("QApplication", (), {})
    qtwidgets_module.QMessageBox = type(
        "QMessageBox",
        (),
        {"critical": staticmethod(lambda *args, **kwargs: None)},
    )
    qtwidgets_module.QMainWindow = type("QMainWindow", (), {})

    sys.modules.setdefault("PySide6", pyside6_module)
    sys.modules["PySide6.QtCore"] = qtcore_module
    sys.modules["PySide6.QtWebEngineWidgets"] = qtwebengine_module
    sys.modules["PySide6.QtWidgets"] = qtwidgets_module


try:
    import PySide6  # noqa: F401
except ImportError:
    _install_pyside6_stub()

import main
import main_window


class FrontendPathTests(unittest.TestCase):
    def test_frontend_path_targets_built_frontend_entrypoint(self):
        expected = (
            Path(__file__).resolve().parent.parent.parent
            / "frontend"
            / "dist"
            / "index.html"
        )

        self.assertEqual(main_window.FRONTEND_PATH, expected)


class MainEntryPointTests(unittest.TestCase):
    @patch("main.QApplication")
    @patch("main.QMessageBox.critical")
    @patch("main.sys.exit")
    def test_main_exits_with_error_when_frontend_is_missing(
        self,
        exit_mock,
        critical_mock,
        app_ctor_mock,
    ):
        exit_mock.side_effect = SystemExit(1)

        with patch.object(main, "FRONTEND_PATH", Path("/tmp/does-not-exist/index.html")):
            with self.assertRaises(SystemExit):
                main.main()

        app_ctor_mock.assert_called_once()
        critical_mock.assert_called_once()
        exit_mock.assert_called_once_with(1)

    @patch("main.MainWindow")
    @patch("main.QApplication")
    @patch("main.QMessageBox.critical")
    @patch("main.sys.exit")
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

        with patch.object(main, "FRONTEND_PATH", Path(__file__).resolve()):
            with self.assertRaises(SystemExit):
                main.main()

        critical_mock.assert_not_called()
        window_ctor_mock.assert_called_once()
        fake_window.show.assert_called_once()
        fake_app.exec.assert_called_once()
        exit_mock.assert_called_once_with(0)
