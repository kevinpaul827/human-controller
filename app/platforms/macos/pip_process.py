"""macos/pip_process.py

Manages macOS picture-in-picture helper process.
"""

import os
import sys
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    QProcess,
    QProcessEnvironment,
    QTimer,
    Signal,
)
from PySide6.QtGui import QImage

from app.utils.logging_utils import log_info

from .pip_protocol import (
    PIP_HELPER_FLAG,
    PROTOCOL_VERSION,
    MappedFrameWriter,
    MessageBuffer,
    encode_message,
)

# Helper-process lifecycle policy. Durations are milliseconds.
HELPER_APP_NAME = "Human Controller PiP.app"
HELPER_EXECUTABLE_NAME = "Human Controller PiP"
HELPER_READY_TIMEOUT_MS = 5000
HELPER_RESTART_LIMIT = 2
HELPER_RESTART_POLL_MS = 100
HELPER_STABLE_READY_MS = 5000
HELPER_TERMINATE_TIMEOUT_MS = 500


def _enum_label(value):
    name = getattr(value, "name", None)
    if name:
        return str(name)
    return str(getattr(value, "value", value))


def _is_not_running(process):
    if process is None:
        return True
    try:
        state = process.state()
    except RuntimeError:
        return True
    return (
        state == QProcess.ProcessState.NotRunning
        or getattr(state, "value", state)
        == QProcess.ProcessState.NotRunning.value
    )


def bundled_helper_executable():
    contents = Path(sys.executable).resolve().parent.parent
    return (
        contents
        / "Helpers"
        / HELPER_APP_NAME
        / "Contents"
        / "MacOS"
        / HELPER_EXECUTABLE_NAME
    )


def build_pip_helper_command(frame_path, parent_pid=None):
    parent_pid = int(parent_pid or os.getpid())
    arguments = [
        PIP_HELPER_FLAG,
        "--frame-file",
        str(frame_path),
        "--parent-pid",
        str(parent_pid),
    ]
    if getattr(sys, "frozen", False):
        return [str(bundled_helper_executable()), *arguments]
    root = Path(__file__).resolve().parents[3]
    return [sys.executable, str(root / "run_app.py"), *arguments]


class MacOSPipProcessTransport(QObject):
    messageReceived = Signal(dict)

    def __init__(self, process_factory=None, frame_writer=None, parent=None):
        super().__init__(parent)
        self.process_factory = process_factory or QProcess
        self.frame_writer = frame_writer or MappedFrameWriter()
        self.process = None
        self.generation = 0
        self.ready = False
        self.shutting_down = False
        self.parser = MessageBuffer()
        self.pending_frame = None
        self.last_frame = None
        self.frame_in_flight = None
        self.frame_send_scheduled = False
        self.disconnect_reported = False
        self.failed_generation = None
        self.ready_timer = None
        self.termination_timer = QTimer(self)
        self.termination_timer.setSingleShot(True)
        self.termination_timer.timeout.connect(self._force_stop_current_process)
        self.terminating_process = None
        self.terminating_generation = None

    def is_running(self):
        return not _is_not_running(self.process)

    def start(self):
        if self.shutting_down or self.is_running():
            return False
        self.generation += 1
        generation = self.generation
        try:
            process = self.process_factory(self)
        except Exception as error:
            self.process = None
            self.ready = False
            self.disconnect_reported = False
            self.failed_generation = generation
            self._report_disconnected(
                f"failed to create helper process: {error!r}",
                generation,
            )
            return False
        self.process = process
        self.ready = False
        self.parser = MessageBuffer()
        self.disconnect_reported = False
        self.failed_generation = None
        process.readyReadStandardOutput.connect(
            lambda current=process, current_generation=generation: self._read_stdout(
                current,
                current_generation,
            )
        )
        process.readyReadStandardError.connect(
            lambda current=process, current_generation=generation: self._read_stderr(
                current,
                current_generation,
            )
        )
        process.finished.connect(
            lambda exit_code,
            exit_status,
            current=process,
            current_generation=generation: self._handle_finished(
                current, current_generation, exit_code, exit_status
            )
        )
        process.errorOccurred.connect(
            lambda error,
            current=process,
            current_generation=generation: self._handle_process_error(
                current, current_generation, error
            )
        )
        self._start_ready_timer(process, generation)
        try:
            command = build_pip_helper_command(self.frame_writer.path)
            if getattr(sys, "frozen", False):
                environment = QProcessEnvironment.systemEnvironment()
                environment.insert("PYINSTALLER_RESET_ENVIRONMENT", "1")
                process.setProcessEnvironment(environment)
            process.start(command[0], command[1:])
        except Exception as error:
            self._fail_process(
                process,
                generation,
                f"failed to launch helper process: {error!r}",
            )
            return False
        return True

    def send(self, payload, require_ready=True):
        if require_ready and not self.ready:
            return False
        if not self.is_running():
            return False
        try:
            encoded = encode_message(payload)
        except (TypeError, ValueError):
            return False
        return self.process.write(encoded) == len(encoded)

    def submit_frame(self, image, timestamp_ms=None):
        if self.shutting_down or image is None or image.isNull():
            return
        frame = (QImage(image), timestamp_ms)
        self.last_frame = frame
        self.pending_frame = frame
        self._schedule_pending_frame()

    def clear_frames(self):
        self.pending_frame = None
        self.last_frame = None

    def _schedule_pending_frame(self):
        if self.frame_send_scheduled:
            return
        self.frame_send_scheduled = True
        QTimer.singleShot(0, self._send_pending_frame)

    def _send_pending_frame(self):
        self.frame_send_scheduled = False
        if (
            self.shutting_down
            or not self.ready
            or self.frame_in_flight is not None
            or self.pending_frame is None
        ):
            return
        image, timestamp_ms = self.pending_frame
        self.pending_frame = None
        metadata = self.frame_writer.write(image, timestamp_ms)
        if metadata is None:
            return
        if not self.send(metadata):
            self.pending_frame = self.last_frame
            return
        self.frame_in_flight = metadata["sequence"]

    def _is_current(self, process, generation):
        return process is self.process and generation == self.generation

    def _read_stdout(self, process, generation):
        if not self._is_current(process, generation):
            return
        chunk = bytes(process.readAllStandardOutput())
        for message in self.parser.feed(chunk):
            self._handle_message(process, generation, message)

    def _read_stderr(self, process, generation):
        if not self._is_current(process, generation):
            return
        output = bytes(process.readAllStandardError()).decode(
            "utf-8",
            errors="replace",
        ).strip()
        if output:
            log_info(f"[pip-helper] {output}")

    def _handle_message(self, process, generation, message):
        if (
            not self._is_current(process, generation)
            or self.shutting_down
            or self.failed_generation == generation
        ):
            return
        message_type = message.get("type")
        if message_type == "ready":
            try:
                protocol = int(message.get("protocol", -1))
            except (TypeError, ValueError, OverflowError):
                protocol = -1
            if protocol != PROTOCOL_VERSION:
                self._fail_process(
                    process,
                    generation,
                    "protocol mismatch",
                )
                return
            if self.ready:
                return
            self.ready = True
            self._stop_ready_timer(process, generation)
            self.messageReceived.emit(
                {**message, "_generation": generation}
            )
            self._schedule_pending_frame()
            return
        if message_type == "frame_consumed":
            try:
                sequence = int(message.get("sequence"))
            except (TypeError, ValueError):
                return
            if self.frame_in_flight == sequence:
                self.frame_in_flight = None
                self._schedule_pending_frame()
            return
        self.messageReceived.emit({**message, "_generation": generation})

    def _handle_finished(
        self,
        process,
        generation,
        exit_code,
        exit_status,
    ):
        if not self._is_current(process, generation):
            return
        self._stop_ready_timer(process, generation)
        self._stop_termination_timer(process, generation)
        self.ready = False
        self.frame_in_flight = None
        if self.last_frame is not None:
            self.pending_frame = self.last_frame
        if not self.shutting_down:
            self._report_disconnected(
                "helper exited with status "
                f"{exit_code} ({_enum_label(exit_status)})",
                generation,
            )

    def _handle_process_error(self, process, generation, error):
        if (
            not self._is_current(process, generation)
            or self.shutting_down
        ):
            return
        self._fail_process(
            process,
            generation,
            f"helper process error {_enum_label(error)}",
        )

    def _start_ready_timer(self, process, generation):
        if self.ready_timer is not None:
            self.ready_timer.stop()
            self.ready_timer.deleteLater()
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(
            lambda current=process,
            current_generation=generation: self._handle_ready_timeout(
                current, current_generation
            )
        )
        self.ready_timer = timer
        timer.start(HELPER_READY_TIMEOUT_MS)

    def _stop_ready_timer(self, process=None, generation=None):
        timer = self.ready_timer
        if timer is None:
            return
        if process is not None and not self._is_current(process, generation):
            return
        timer.stop()

    def _handle_ready_timeout(self, process, generation):
        if (
            not self._is_current(process, generation)
            or self.ready
            or self.shutting_down
        ):
            return
        self._fail_process(
            process,
            generation,
            "helper readiness timed out",
        )

    def _fail_process(self, process, generation, reason):
        if (
            not self._is_current(process, generation)
            or self.shutting_down
            or self.failed_generation == generation
        ):
            return
        self.failed_generation = generation
        self.ready = False
        self.frame_in_flight = None
        if self.last_frame is not None:
            self.pending_frame = self.last_frame
        self._stop_ready_timer(process, generation)
        self._report_disconnected(reason, generation)
        if not _is_not_running(process):
            self.terminating_process = process
            self.terminating_generation = generation
            process.terminate()
            self.termination_timer.start(HELPER_TERMINATE_TIMEOUT_MS)

    def _force_stop_current_process(self):
        process = self.terminating_process
        generation = self.terminating_generation
        if (
            process is None
            or not self._is_current(process, generation)
            or _is_not_running(process)
        ):
            return
        process.kill()

    def _stop_termination_timer(self, process=None, generation=None):
        if (
            process is not None
            and (
                process is not self.terminating_process
                or generation != self.terminating_generation
            )
        ):
            return
        self.termination_timer.stop()
        self.terminating_process = None
        self.terminating_generation = None

    def _report_disconnected(self, reason, generation=None):
        if generation is None:
            generation = self.generation
        if generation != self.generation:
            return
        if self.disconnect_reported:
            return
        self.disconnect_reported = True
        self.messageReceived.emit(
            {
                "type": "disconnected",
                "reason": str(reason),
                "_generation": generation,
            }
        )

    def shutdown(self):
        if self.shutting_down:
            return
        self.shutting_down = True
        self._stop_ready_timer()
        self._stop_termination_timer()
        self.pending_frame = None
        self.last_frame = None
        process = self.process
        if not _is_not_running(process):
            self.send({"type": "shutdown"}, require_ready=False)
            process.waitForBytesWritten(250)
            if not process.waitForFinished(1500):
                process.terminate()
                if not process.waitForFinished(500):
                    process.kill()
                    process.waitForFinished(500)
        self.ready = False
        self.frame_in_flight = None
        self.process = None
        self.frame_writer.close()


class MacOSPictureInPictureProxy(QObject):
    def __init__(self, transport=None, parent=None):
        super().__init__(parent)
        self.transport = transport or MacOSPipProcessTransport(parent=self)
        self.transport.messageReceived.connect(self._handle_message)
        self.visible = False
        self.pose = {}
        self.shutting_down = False
        self.restart_attempts = 0
        self.restart_timer = QTimer(self)
        self.restart_timer.setSingleShot(True)
        self.restart_timer.timeout.connect(self._restart_helper)
        self.stable_timer = QTimer(self)
        self.stable_timer.setSingleShot(True)
        self.stable_timer.timeout.connect(self._mark_helper_stable)

    def set_frame(self, image, timestamp_ms=None):
        if self.visible and not self.shutting_down:
            self.transport.submit_frame(image, timestamp_ms)

    def set_pose(self, payload):
        self.pose = dict(payload or {})
        if self.visible and self.transport.ready:
            self.transport.send({"type": "pose", "payload": self.pose})

    def show_match(self, payload):
        if self.visible and self.transport.ready:
            self.transport.send(
                {"type": "match", "payload": dict(payload or {})}
            )

    def clear(self):
        self.pose = {}
        self.transport.clear_frames()
        if self.transport.ready:
            self.transport.send({"type": "clear"})

    def show_overlay(self):
        if self.shutting_down:
            return
        was_visible = self.visible
        self.visible = True
        if not was_visible:
            self.restart_attempts = 0
            self.restart_timer.stop()
            self.stable_timer.stop()
        if not self.transport.is_running():
            self.transport.start()
        elif self.transport.ready:
            self.transport.send({"type": "show"})

    def hide_overlay(self):
        self.visible = False
        self.restart_attempts = 0
        self.restart_timer.stop()
        self.stable_timer.stop()
        if self.transport.ready:
            self.transport.send({"type": "hide"})

    def isVisible(self):
        return self.visible

    def shutdown(self):
        if self.shutting_down:
            return
        self.shutting_down = True
        self.restart_timer.stop()
        self.stable_timer.stop()
        self.visible = False
        self.transport.shutdown()

    def _handle_message(self, message):
        if self.shutting_down or self._is_stale_message(message):
            return
        message_type = message.get("type")
        if message_type == "ready":
            self.transport.send(
                {
                    "type": "sync",
                    "visible": self.visible,
                    "pose": self.pose,
                }
            )
            if self.restart_attempts:
                self.stable_timer.start(HELPER_STABLE_READY_MS)
            return
        if message_type == "disconnected":
            if self.shutting_down or not self.visible:
                return
            self.stable_timer.stop()
            if self.restart_attempts >= HELPER_RESTART_LIMIT:
                log_info(
                    "[pip-helper] unavailable after repeated restart attempts: "
                    f"{message.get('reason', 'unknown error')}"
                )
                self.visible = False
                self.restart_timer.stop()
                return
            self.restart_attempts += 1
            self.restart_timer.start(250 * self.restart_attempts)

    def _restart_helper(self):
        if self.shutting_down or not self.visible:
            return
        if self.transport.ready:
            return
        if self.transport.start():
            return
        if self.transport.is_running():
            self.restart_timer.start(HELPER_RESTART_POLL_MS)

    def _mark_helper_stable(self):
        if (
            not self.shutting_down
            and self.visible
            and self.transport.ready
        ):
            self.restart_attempts = 0

    def _is_stale_message(self, message):
        generation = message.get("_generation")
        transport_generation = getattr(self.transport, "generation", None)
        if generation is None or transport_generation is None:
            return False
        try:
            return int(generation) != int(transport_generation)
        except (TypeError, ValueError, OverflowError):
            return True
