import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from app.platforms.macos import pip_helper
from app.platforms.macos.pip_helper import MacOSPipHelperController
from app.platforms.macos.pip_protocol import PROTOCOL_VERSION
from app.tests._bootstrap import ensure_qapplication


class FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class FakeApplication:
    def __init__(self):
        self.aboutToQuit = FakeSignal()
        self.quit = MagicMock()


class FakeWindow:
    def __init__(self):
        self.pose_calls = []
        self.match_calls = []
        self.frame_calls = []
        self.clear_count = 0
        self.show_count = 0
        self.hide_count = 0
        self.shutdown_count = 0

    def set_pose(self, payload):
        self.pose_calls.append(payload)

    def show_match(self, payload):
        self.match_calls.append(payload)

    def set_frame(self, image, timestamp_ms=None):
        self.frame_calls.append((image, timestamp_ms))

    def clear(self):
        self.clear_count += 1

    def show_overlay(self):
        self.show_count += 1

    def hide_overlay(self):
        self.hide_count += 1

    def shutdown(self):
        self.shutdown_count += 1


class FakeReader:
    def __init__(self):
        self.result = None
        self.read_calls = []
        self.close_count = 0

    def read(self, metadata):
        self.read_calls.append(metadata)
        return self.result

    def close(self):
        self.close_count += 1


class FakeNotifier:
    class Type:
        Read = object()

    def __init__(self, descriptor, notifier_type, parent):
        self.descriptor = descriptor
        self.notifier_type = notifier_type
        self.parent = parent
        self.activated = FakeSignal()
        self.enabled = True

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)


class FakeTimer:
    def __init__(self, parent):
        self.parent = parent
        self.timeout = FakeSignal()
        self.intervals = []
        self.stop_count = 0

    def start(self, interval):
        self.intervals.append(interval)

    def stop(self):
        self.stop_count += 1


class MacOSPipHelperControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_application = ensure_qapplication()

    def setUp(self):
        self.app = FakeApplication()
        self.window = FakeWindow()
        self.reader = FakeReader()
        with (
            patch.object(
                pip_helper,
                "MappedFrameReader",
                return_value=self.reader,
            ),
            patch.object(pip_helper, "QSocketNotifier", FakeNotifier),
            patch.object(pip_helper, "QTimer", FakeTimer),
            patch.object(pip_helper.os, "set_blocking"),
        ):
            self.controller = MacOSPipHelperController(
                self.app,
                "/tmp/frame-buffer",
                1234,
                input_fd=10,
                output_fd=11,
                window_factory=lambda: self.window,
            )

    def tearDown(self):
        self.controller.close()

    def test_start_announces_matching_protocol_version(self):
        with patch.object(
            self.controller,
            "_send",
            return_value=True,
        ) as send:
            self.controller.start()

        send.assert_called_once_with(
            {"type": "ready", "protocol": PROTOCOL_VERSION}
        )

    def test_sync_and_visibility_commands_are_dispatched(self):
        self.controller._handle_message(
            {
                "type": "sync",
                "visible": True,
                "pose": {"detected": True},
            }
        )
        self.controller._handle_message({"type": "hide"})

        self.assertEqual(
            self.window.pose_calls,
            [{"detected": True}],
        )
        self.assertEqual(self.window.show_count, 1)
        self.assertEqual(self.window.hide_count, 1)

    def test_pose_match_and_clear_commands_are_dispatched(self):
        self.controller._handle_message(
            {"type": "pose", "payload": {"detected": True}}
        )
        self.controller._handle_message(
            {"type": "match", "payload": {"matched": True}}
        )
        self.controller._handle_message({"type": "clear"})

        self.assertEqual(
            self.window.pose_calls,
            [{"detected": True}],
        )
        self.assertEqual(
            self.window.match_calls,
            [{"matched": True}],
        )
        self.assertEqual(self.window.clear_count, 1)

    def test_valid_frame_is_applied_and_acknowledged(self):
        image = QImage(2, 2, QImage.Format.Format_RGBA8888)
        self.reader.result = (image, 91)
        message = {"type": "frame", "sequence": 7}

        with patch.object(
            self.controller,
            "_send",
            return_value=True,
        ) as send:
            self.controller._handle_message(message)

        self.assertEqual(self.reader.read_calls, [message])
        self.assertEqual(self.window.frame_calls, [(image, 91)])
        send.assert_called_once_with(
            {"type": "frame_consumed", "sequence": 7}
        )

    def test_invalid_frame_is_acknowledged_without_updating_window(self):
        message = {"type": "frame", "sequence": 9}

        with patch.object(
            self.controller,
            "_send",
            return_value=True,
        ) as send:
            self.controller._handle_message(message)

        self.assertEqual(self.window.frame_calls, [])
        send.assert_called_once_with(
            {"type": "frame_consumed", "sequence": 9}
        )

    def test_shutdown_closes_window_and_quits(self):
        with patch.object(
            self.controller,
            "_send",
            return_value=True,
        ) as send:
            self.controller._handle_message({"type": "shutdown"})

        self.assertEqual(self.window.shutdown_count, 1)
        send.assert_not_called()
        self.app.quit.assert_called_once_with()

    def test_input_eof_and_missing_parent_quit_helper(self):
        with patch.object(pip_helper.os, "read", return_value=b""):
            self.controller._read_input()

        with patch.object(
            pip_helper.os,
            "kill",
            side_effect=ProcessLookupError,
        ):
            self.controller._check_parent()

        self.assertEqual(self.app.quit.call_count, 2)

    def test_close_is_idempotent_and_releases_resources(self):
        self.controller.close()
        self.controller.close()

        self.assertEqual(self.reader.close_count, 1)
        self.assertFalse(self.controller.input_notifier.enabled)
        self.assertEqual(self.controller.parent_timer.stop_count, 1)

    def test_qapplication_exists_before_accessory_policy_is_applied(self):
        events = []
        application = MagicMock()
        application.exec.return_value = 17
        controller = MagicMock()

        with (
            patch.object(
                pip_helper,
                "QApplication",
                side_effect=lambda _argv: events.append("application")
                or application,
            ),
            patch.object(
                pip_helper,
                "set_overlay_activation_policy",
                side_effect=lambda _enabled: events.append("policy") or True,
            ),
            patch.object(
                pip_helper,
                "MacOSPipHelperController",
                side_effect=lambda *_args: events.append("controller")
                or controller,
            ),
        ):
            result = pip_helper.run_pip_helper("/tmp/frame-buffer", 1234)

        self.assertEqual(events, ["application", "policy", "controller"])
        self.assertEqual(result, 17)
        application.setQuitOnLastWindowClosed.assert_called_once_with(False)
        controller.start.assert_called_once_with()

    def test_frozen_helper_uses_bundle_accessory_policy(self):
        application = MagicMock()
        application.exec.return_value = 19
        controller = MagicMock()

        with (
            patch.object(pip_helper.sys, "frozen", True, create=True),
            patch.object(
                pip_helper,
                "QApplication",
                return_value=application,
            ),
            patch.object(
                pip_helper,
                "set_overlay_activation_policy",
            ) as set_policy,
            patch.object(
                pip_helper,
                "MacOSPipHelperController",
                return_value=controller,
            ),
        ):
            result = pip_helper.run_pip_helper("/tmp/frame-buffer", 1234)

        self.assertEqual(result, 19)
        set_policy.assert_not_called()
        application.setQuitOnLastWindowClosed.assert_called_once_with(False)
        controller.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
