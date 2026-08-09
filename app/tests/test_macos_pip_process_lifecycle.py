import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QProcess, Signal
from PySide6.QtWidgets import QApplication

from app.platforms.macos.pip_process import (
    MacOSPictureInPictureProxy,
    MacOSPipProcessTransport,
)
from app.platforms.macos.pip_protocol import MessageBuffer
from app.tests._bootstrap import ensure_qapplication


class FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class FakeProcess:
    def __init__(self, _parent=None):
        self.readyReadStandardOutput = FakeSignal()
        self.readyReadStandardError = FakeSignal()
        self.finished = FakeSignal()
        self.errorOccurred = FakeSignal()
        self.current_state = QProcess.ProcessState.NotRunning
        self.started = []
        self.writes = []
        self.environments = []
        self.stdout = b""
        self.stderr = b""
        self.terminate_count = 0
        self.kill_count = 0
        self.wait_for_bytes_count = 0
        self.wait_results = []

    def state(self):
        return self.current_state

    def start(self, executable, arguments):
        self.started.append((executable, list(arguments)))
        self.current_state = QProcess.ProcessState.Running

    def setProcessEnvironment(self, environment):
        self.environments.append(environment)

    def write(self, payload):
        encoded = bytes(payload)
        self.writes.append(encoded)
        return len(encoded)

    def readAllStandardOutput(self):
        output = self.stdout
        self.stdout = b""
        return output

    def readAllStandardError(self):
        output = self.stderr
        self.stderr = b""
        return output

    def terminate(self):
        self.terminate_count += 1

    def kill(self):
        self.kill_count += 1
        self.current_state = QProcess.ProcessState.NotRunning

    def waitForBytesWritten(self, _timeout):
        self.wait_for_bytes_count += 1
        return True

    def waitForFinished(self, _timeout):
        result = self.wait_results.pop(0) if self.wait_results else True
        if result:
            self.current_state = QProcess.ProcessState.NotRunning
        return result


class FakeFrameWriter:
    def __init__(self):
        self.path = "/tmp/human-controller-test-frame"
        self.close_count = 0

    def write(self, _image, _timestamp_ms=None):
        return None

    def close(self):
        self.close_count += 1


class FakeTransport(QObject):
    messageReceived = Signal(dict)

    def __init__(self):
        super().__init__()
        self.generation = 2
        self.ready = True
        self.running = True
        self.sent = []
        self.shutdown_count = 0

    def send(self, payload, require_ready=True):
        self.sent.append((dict(payload), require_ready))
        return True

    def start(self):
        return False

    def is_running(self):
        return self.running

    def submit_frame(self, _image, _timestamp_ms=None):
        return None

    def clear_frames(self):
        return None

    def shutdown(self):
        self.shutdown_count += 1


class MacOSPipProcessLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = ensure_qapplication()

    def make_transport(self):
        processes = []

        def factory(parent):
            process = FakeProcess(parent)
            processes.append(process)
            return process

        writer = FakeFrameWriter()
        transport = MacOSPipProcessTransport(
            process_factory=factory,
            frame_writer=writer,
        )
        return transport, processes, writer

    def test_process_error_formats_qt_enum_and_reports_once(self):
        transport, processes, _writer = self.make_transport()
        messages = []
        transport.messageReceived.connect(messages.append)
        self.assertTrue(transport.start())
        process = processes[0]
        process.current_state = QProcess.ProcessState.NotRunning

        transport._handle_process_error(
            process,
            transport.generation,
            QProcess.ProcessError.FailedToStart,
        )
        transport._handle_finished(
            process,
            transport.generation,
            -1,
            QProcess.ExitStatus.CrashExit,
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["type"], "disconnected")
        self.assertIn("FailedToStart", messages[0]["reason"])
        transport.shutdown()

    def test_timeout_invalidates_generation_and_restart_waits_for_exit(self):
        transport, processes, _writer = self.make_transport()
        proxy = MacOSPictureInPictureProxy(transport=transport)
        proxy.show_overlay()
        first = processes[0]
        first_generation = transport.generation

        transport._handle_ready_timeout(first, first_generation)

        self.assertFalse(transport.ready)
        self.assertEqual(first.terminate_count, 1)
        self.assertEqual(proxy.restart_attempts, 1)
        transport._handle_message(
            first,
            first_generation,
            {"type": "ready", "protocol": 1},
        )
        self.assertFalse(transport.ready)

        proxy.restart_timer.stop()
        proxy._restart_helper()
        self.assertEqual(len(processes), 1)
        self.assertTrue(proxy.restart_timer.isActive())

        transport._force_stop_current_process()
        first.finished.emit(-1, QProcess.ExitStatus.CrashExit)
        proxy.restart_timer.stop()
        proxy._restart_helper()

        self.assertEqual(len(processes), 2)
        second = processes[1]
        second_generation = transport.generation
        transport._handle_message(
            first,
            first_generation,
            {"type": "ready", "protocol": 1},
        )
        self.assertFalse(transport.ready)
        transport._handle_message(
            second,
            second_generation,
            {"type": "ready", "protocol": 1},
        )
        self.assertTrue(transport.ready)
        parser = MessageBuffer()
        sent = [
            message
            for payload in second.writes
            for message in parser.feed(payload)
        ]
        self.assertEqual(sent[-1]["type"], "sync")
        proxy.shutdown()

    def test_stale_proxy_event_is_ignored_and_stable_ready_resets_budget(self):
        transport = FakeTransport()
        proxy = MacOSPictureInPictureProxy(transport=transport)
        proxy.visible = True
        proxy.restart_attempts = 2

        transport.messageReceived.emit(
            {
                "type": "disconnected",
                "reason": "old process",
                "_generation": 1,
            }
        )

        self.assertEqual(proxy.restart_attempts, 2)
        transport.messageReceived.emit(
            {"type": "ready", "protocol": 1, "_generation": 2}
        )
        self.assertTrue(proxy.stable_timer.isActive())
        proxy._mark_helper_stable()
        self.assertEqual(proxy.restart_attempts, 0)
        proxy.shutdown()

    def test_shutdown_escalates_and_is_idempotent(self):
        transport, processes, writer = self.make_transport()
        self.assertTrue(transport.start())
        process = processes[0]
        process.wait_results = [False, False, True]

        transport.shutdown()
        transport.shutdown()

        parser = MessageBuffer()
        sent = [
            message
            for payload in process.writes
            for message in parser.feed(payload)
        ]
        self.assertEqual(sent, [{"type": "shutdown"}])
        self.assertEqual(process.wait_for_bytes_count, 1)
        self.assertEqual(process.terminate_count, 1)
        self.assertEqual(process.kill_count, 1)
        self.assertEqual(writer.close_count, 1)
        self.assertIsNone(transport.process)
        self.assertFalse(transport.ready)


if __name__ == "__main__":
    unittest.main()
