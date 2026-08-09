import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.tests.test_bootstrap import import_main_modules_with_stubs


main, main_window = import_main_modules_with_stubs()


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
    ):
        fake_app = MagicMock()
        fake_app.exec.return_value = 0
        fake_window = MagicMock()
        app_ctor_mock.return_value = fake_app
        window_ctor_mock.return_value = fake_window

        with patch.object(main.sys, "platform", "darwin"):
            with patch.object(main, "frontend_source_exists", return_value=True):
                self.assertEqual(main.main(), 0)

        critical_mock.assert_not_called()
        window_ctor_mock.assert_called_once()
        fake_window.show.assert_called_once()
        fake_app.exec.assert_called_once()
        fake_window.shutdown.assert_called_once()
        exit_mock.assert_not_called()


class MainWindowCloseTests(unittest.TestCase):
    def test_close_uses_normal_shutdown_path(self):
        window = MagicMock()
        event = MagicMock()

        with patch.object(
            main_window.QMainWindow,
            "closeEvent",
            create=True,
        ) as base_close:
            main_window.MainWindow.closeEvent(window, event)

        window.shutdown.assert_called_once()
        base_close.assert_called_once_with(window, event)
