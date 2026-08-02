import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QProcess
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from app.platforms.macos import pip_process
from app.platforms.macos.pip_process import (
    HELPER_RESTART_LIMIT,
    HELPER_RESTART_POLL_MS,
    MacOSPictureInPictureProxy,
    MacOSPipProcessTransport,
    build_pip_helper_command,
)
from app.platforms.macos.pip_protocol import MessageBuffer


class FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class FakeTransport:
    def __init__(self):
        self.messageReceived = FakeSignal()
        self.ready = False
        self.running = False
        self.generation = 0
        self.start_result = True
        self.start_count = 0
        self.shutdown_count = 0
        self.sent = []
        self.frames = []
        self.clear_count = 0

    def is_running(self):
        return self.running

    def start(self):
        self.start_count += 1
        if not self.start_result:
            return False
        self.generation += 1
        self.running = True
        return True

    def send(self, payload, require_ready=True):
        if require_ready and not self.ready:
            return False
        self.sent.append(dict(payload))
        return True

    def submit_frame(self, image, timestamp_ms=None):
        self.frames.append((image, timestamp_ms))

    def clear_frames(self):
        self.clear_count += 1

    def shutdown(self):
        self.shutdown_count += 1
        self.running = False


class FakeFrameWriter:
    def __init__(self):
        self.path = "/tmp/human-controller-test-frame"
        self.timestamps = []
        self.close_count = 0

    def write(self, _image, timestamp_ms=None):
        self.timestamps.append(timestamp_ms)
        return {
            "type": "frame",
            "sequence": len(self.timestamps),
        }

    def close(self):
        self.close_count += 1


class FakeProcess:
    def __init__(self):
        self.running = True
        self.writes = []
        self.wait_results = []
        self.wait_calls = []
        self.terminate_count = 0
        self.kill_count = 0
        self.wait_for_bytes_written = []

    def state(self):
        if self.running:
            return QProcess.ProcessState.Running
        return QProcess.ProcessState.NotRunning

    def write(self, payload):
        self.writes.append(bytes(payload))
        return len(payload)

    def waitForBytesWritten(self, timeout_ms):
        self.wait_for_bytes_written.append(timeout_ms)
        return True

    def waitForFinished(self, timeout_ms):
        self.wait_calls.append(timeout_ms)
        if self.wait_results:
            return self.wait_results.pop(0)
        return True

    def terminate(self):
        self.terminate_count += 1

    def kill(self):
        self.kill_count += 1


class MacOSPictureInPictureProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.transport = FakeTransport()
        self.proxy = MacOSPictureInPictureProxy(self.transport)

    def tearDown(self):
        self.proxy.restart_timer.stop()
        self.proxy.shutdown()

    def test_session_visibility_commands_update_proxy_state(self):
        self.proxy.show_overlay()

        self.assertTrue(self.proxy.isVisible())
        self.assertEqual(self.transport.start_count, 1)

        self.transport.ready = True
        self.proxy.hide_overlay()

        self.assertFalse(self.proxy.isVisible())
        self.assertEqual(self.transport.sent[-1], {"type": "hide"})

    def test_ready_message_synchronizes_requested_visibility_and_pose(self):
        pose = {"detected": True, "timestampMs": 17}
        self.proxy.set_pose(pose)
        self.proxy.show_overlay()
        self.transport.ready = True

        self.transport.messageReceived.emit(
            {"type": "ready", "protocol": 1}
        )

        self.assertEqual(
            self.transport.sent,
            [{"type": "sync", "visible": True, "pose": pose}],
        )

    def test_hidden_proxy_does_not_forward_frames(self):
        image = QImage(2, 2, QImage.Format.Format_RGBA8888)
        image.fill(QColor("red"))

        self.proxy.set_frame(image, 1)
        self.proxy.show_overlay()
        self.proxy.set_frame(image, 2)

        self.assertEqual(self.transport.frames, [(image, 2)])

    def test_disconnect_restarts_only_during_live_overlay_lifecycle(self):
        self.proxy.show_overlay()
        self.transport.running = False

        with patch.object(self.proxy.restart_timer, "start") as start_timer:
            self.transport.messageReceived.emit(
                {"type": "disconnected", "reason": "crashed"}
            )

        start_timer.assert_called_once_with(250)
        self.assertEqual(self.proxy.restart_attempts, 1)
        self.proxy._restart_helper()
        self.assertEqual(self.transport.start_count, 2)

        self.proxy.hide_overlay()
        self.transport.running = False
        self.proxy._restart_helper()
        self.assertEqual(self.transport.start_count, 2)

    def test_restart_polls_until_failed_process_has_exited(self):
        self.proxy.visible = True
        self.transport.running = True
        self.transport.start_result = False

        with patch.object(self.proxy.restart_timer, "start") as start_timer:
            self.proxy._restart_helper()

        self.assertEqual(self.transport.start_count, 1)
        start_timer.assert_called_once_with(HELPER_RESTART_POLL_MS)

    @patch.object(pip_process, "log_info")
    def test_restart_limit_turns_terminal_failure_into_invisible_state(
        self,
        log_info,
    ):
        self.proxy.show_overlay()
        self.proxy.restart_attempts = HELPER_RESTART_LIMIT

        self.transport.messageReceived.emit(
            {"type": "disconnected", "reason": "still failing"}
        )

        self.assertFalse(self.proxy.isVisible())
        log_info.assert_called_once()

    @patch.object(pip_process, "log_info")
    def test_new_session_show_after_terminal_failure_resets_restart_budget(
        self,
        _log_info,
    ):
        self.proxy.show_overlay()
        self.proxy.restart_attempts = HELPER_RESTART_LIMIT
        self.transport.messageReceived.emit(
            {"type": "disconnected", "reason": "still failing"}
        )
        self.transport.running = False

        self.proxy.show_overlay()

        self.assertTrue(self.proxy.isVisible())
        self.assertEqual(self.proxy.restart_attempts, 0)
        self.assertEqual(self.transport.start_count, 2)

    def test_shutdown_is_idempotent_and_prevents_restart(self):
        self.proxy.show_overlay()

        self.proxy.shutdown()
        self.proxy.shutdown()
        self.transport.running = False
        self.proxy._restart_helper()

        self.assertEqual(self.transport.shutdown_count, 1)
        self.assertEqual(self.transport.start_count, 1)
        self.assertFalse(self.proxy.isVisible())


class MacOSPipProcessTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_pending_frames_coalesce_to_latest_without_blocking_control(self):
        writer = FakeFrameWriter()
        process = FakeProcess()
        transport = MacOSPipProcessTransport(frame_writer=writer)
        transport.process = process
        transport.ready = True
        first = QImage(2, 2, QImage.Format.Format_RGBA8888)
        second = QImage(2, 2, QImage.Format.Format_RGBA8888)
        third = QImage(2, 2, QImage.Format.Format_RGBA8888)

        with patch.object(pip_process.QTimer, "singleShot"):
            transport.submit_frame(first, 1)
            transport._send_pending_frame()
            transport.submit_frame(second, 2)
            transport.submit_frame(third, 3)
            transport._send_pending_frame()
            self.assertTrue(transport.send({"type": "hide"}))
            transport._handle_message(
                process,
                transport.generation,
                {"type": "frame_consumed", "sequence": 1},
            )
            transport._send_pending_frame()

        messages = MessageBuffer().feed(b"".join(process.writes))
        self.assertEqual(writer.timestamps, [1, 3])
        self.assertEqual(
            messages,
            [
                {"type": "frame", "sequence": 1},
                {"type": "hide"},
                {"type": "frame", "sequence": 2},
            ],
        )

    def test_shutdown_escalates_and_releases_frame_transport_once(self):
        writer = FakeFrameWriter()
        process = FakeProcess()
        process.wait_results = [False, False, True]
        transport = MacOSPipProcessTransport(frame_writer=writer)
        transport.process = process
        transport.ready = True

        transport.shutdown()
        transport.shutdown()

        messages = MessageBuffer().feed(b"".join(process.writes))
        self.assertEqual(messages, [{"type": "shutdown"}])
        self.assertEqual(process.wait_for_bytes_written, [250])
        self.assertEqual(process.wait_calls, [1500, 500, 500])
        self.assertEqual(process.terminate_count, 1)
        self.assertEqual(process.kill_count, 1)
        self.assertEqual(writer.close_count, 1)

    def test_protocol_mismatch_reports_disconnect_and_terminates_helper(self):
        writer = FakeFrameWriter()
        process = FakeProcess()
        transport = MacOSPipProcessTransport(frame_writer=writer)
        transport.process = process
        messages = []
        transport.messageReceived.connect(messages.append)

        transport._handle_message(
            process,
            transport.generation,
            {"type": "ready", "protocol": -1},
        )

        self.assertEqual(messages[0]["type"], "disconnected")
        self.assertIn("protocol mismatch", messages[0]["reason"])
        self.assertEqual(process.terminate_count, 1)
        transport.shutdown()

    def test_messages_from_old_process_generation_are_ignored(self):
        writer = FakeFrameWriter()
        current_process = FakeProcess()
        old_process = FakeProcess()
        transport = MacOSPipProcessTransport(frame_writer=writer)
        transport.process = current_process
        transport.generation = 2
        messages = []
        transport.messageReceived.connect(messages.append)

        transport._handle_message(
            old_process,
            1,
            {"type": "ready", "protocol": 1},
        )

        self.assertFalse(transport.ready)
        self.assertEqual(messages, [])
        transport.shutdown()

    def test_development_command_routes_through_run_app(self):
        with patch.object(pip_process.sys, "frozen", False, create=True):
            command = build_pip_helper_command("/tmp/frame-map", 123)

        self.assertEqual(command[0], pip_process.sys.executable)
        self.assertEqual(Path(command[1]).name, "run_app.py")
        self.assertEqual(
            command[2:],
            [
                "--pip-helper",
                "--frame-file",
                "/tmp/frame-map",
                "--parent-pid",
                "123",
            ],
        )

    def test_frozen_command_requires_the_nested_accessory_helper(self):
        helper = Path("/Applications/Human Controller PiP.app/helper")
        with (
            patch.object(pip_process.sys, "frozen", True, create=True),
            patch.object(
                pip_process,
                "bundled_helper_executable",
                return_value=helper,
            ),
        ):
            command = build_pip_helper_command("/tmp/frame-map", 456)

        self.assertEqual(command[0], str(helper))
        self.assertEqual(
            command[1:],
            [
                "--pip-helper",
                "--frame-file",
                "/tmp/frame-map",
                "--parent-pid",
                "456",
            ],
        )


if __name__ == "__main__":
    unittest.main()
