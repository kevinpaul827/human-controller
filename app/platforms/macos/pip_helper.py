import argparse
import os
import sys

from PySide6.QtCore import QObject, QSocketNotifier, QTimer
from PySide6.QtWidgets import QApplication

from app.logging_utils import log_info
from app.picture_in_picture_window import PictureInPictureWindow

from .pip_protocol import (
    PROTOCOL_VERSION,
    MappedFrameReader,
    MessageBuffer,
    encode_message,
)
from .windowing import set_overlay_activation_policy


class MacOSPipHelperController(QObject):
    def __init__(
        self,
        app,
        frame_path,
        parent_pid,
        input_fd=0,
        output_fd=1,
        window_factory=None,
        parent=None,
    ):
        super().__init__(parent)
        self.app = app
        self.parent_pid = int(parent_pid)
        self.input_fd = input_fd
        self.output_fd = output_fd
        self.reader = MappedFrameReader(frame_path)
        self.parser = MessageBuffer()
        self.closed = False
        self.window = (window_factory or PictureInPictureWindow)()
        os.set_blocking(self.input_fd, False)
        self.input_notifier = QSocketNotifier(
            self.input_fd,
            QSocketNotifier.Type.Read,
            self,
        )
        self.input_notifier.activated.connect(self._read_input)
        self.parent_timer = QTimer(self)
        self.parent_timer.timeout.connect(self._check_parent)
        self.parent_timer.start(2000)
        self.app.aboutToQuit.connect(self.close)

    def start(self):
        self._send({"type": "ready", "protocol": PROTOCOL_VERSION})

    def _read_input(self, *_args):
        try:
            chunk = os.read(self.input_fd, 64 * 1024)
        except BlockingIOError:
            return
        except OSError:
            self.app.quit()
            return
        if not chunk:
            self.app.quit()
            return
        for message in self.parser.feed(chunk):
            self._handle_message(message)

    def _handle_message(self, message):
        message_type = message.get("type")
        if message_type == "sync":
            self.window.set_pose(dict(message.get("pose") or {}))
            self._set_visible(bool(message.get("visible")))
            return
        if message_type == "show":
            self._set_visible(True)
            return
        if message_type == "hide":
            self._set_visible(False)
            return
        if message_type == "pose":
            self.window.set_pose(dict(message.get("payload") or {}))
            return
        if message_type == "match":
            self.window.show_match(dict(message.get("payload") or {}))
            return
        if message_type == "clear":
            self.window.clear()
            return
        if message_type == "frame":
            frame = self.reader.read(message)
            if frame is not None:
                image, timestamp_ms = frame
                self.window.set_frame(image, timestamp_ms)
            self._send(
                {
                    "type": "frame_consumed",
                    "sequence": message.get("sequence"),
                }
            )
            return
        if message_type == "shutdown":
            self.window.shutdown()
            self.app.quit()

    def _set_visible(self, visible):
        if visible:
            self.window.show_overlay()
        else:
            self.window.hide_overlay()

    def _check_parent(self):
        try:
            os.kill(self.parent_pid, 0)
        except ProcessLookupError:
            self.app.quit()
        except PermissionError:
            return

    def _send(self, payload):
        try:
            encoded = encode_message(payload)
            offset = 0
            while offset < len(encoded):
                written = os.write(self.output_fd, encoded[offset:])
                if written <= 0:
                    raise BrokenPipeError
                offset += written
            return True
        except (BrokenPipeError, OSError, TypeError, ValueError):
            self.app.quit()
            return False

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.parent_timer.stop()
        self.input_notifier.setEnabled(False)
        self.reader.close()


def run_pip_helper(frame_path, parent_pid):
    app = QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)
    if (
        not getattr(sys, "frozen", False)
        and not set_overlay_activation_policy(True)
    ):
        log_info("[pip-helper] accessory activation policy was unavailable")
    controller = MacOSPipHelperController(
        app,
        frame_path,
        parent_pid,
    )
    controller.start()
    return app.exec()


def run_pip_helper_from_argv(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--frame-file", required=True)
    parser.add_argument("--parent-pid", required=True, type=int)
    arguments = parser.parse_args(list(argv))
    return run_pip_helper(arguments.frame_file, arguments.parent_pid)
