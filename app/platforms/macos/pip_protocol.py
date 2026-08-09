import json
import mmap
import os
import tempfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from app.pip_protocol import PIP_HELPER_FLAG

# This module is the source of truth for the parent/helper IPC contract.
PROTOCOL_VERSION = 1
MESSAGE_PREFIX = b"HC_PIP:"
MAX_MESSAGE_BYTES = 512 * 1024
FRAME_MAX_EDGE = 1280
FRAME_CAPACITY = FRAME_MAX_EDGE * FRAME_MAX_EDGE * 4


def _json_default(value):
    to_list = getattr(value, "tolist", None)
    if callable(to_list):
        return to_list()
    to_item = getattr(value, "item", None)
    if callable(to_item):
        return to_item()
    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serializable"
    )


def encode_message(payload):
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_json_default,
    ).encode("utf-8")
    if len(encoded) > MAX_MESSAGE_BYTES:
        raise ValueError("PiP control message is too large")
    return MESSAGE_PREFIX + encoded + b"\n"


class MessageBuffer:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, chunk):
        if chunk:
            self.buffer.extend(bytes(chunk))
        messages = []
        while True:
            newline = self.buffer.find(b"\n")
            if newline < 0:
                if len(self.buffer) > MAX_MESSAGE_BYTES + len(MESSAGE_PREFIX):
                    self.buffer.clear()
                break
            line = bytes(self.buffer[:newline])
            del self.buffer[: newline + 1]
            if not line.startswith(MESSAGE_PREFIX):
                continue
            encoded = line[len(MESSAGE_PREFIX) :]
            if not encoded or len(encoded) > MAX_MESSAGE_BYTES:
                continue
            try:
                payload = json.loads(encoded.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                messages.append(payload)
        return messages


class MappedFrameWriter:
    def __init__(self, capacity=FRAME_CAPACITY):
        descriptor, path = tempfile.mkstemp(prefix="human-controller-pip-")
        os.fchmod(descriptor, 0o600)
        os.ftruncate(descriptor, capacity)
        self.path = path
        self.capacity = capacity
        self.file = os.fdopen(descriptor, "r+b", buffering=0)
        self.mapping = mmap.mmap(
            self.file.fileno(),
            capacity,
            access=mmap.ACCESS_WRITE,
        )
        self.sequence = 0
        self.closed = False

    def write(self, image, timestamp_ms=None):
        if image is None or image.isNull():
            return None
        frame = QImage(image)
        if frame.width() > FRAME_MAX_EDGE or frame.height() > FRAME_MAX_EDGE:
            frame = frame.scaled(
                FRAME_MAX_EDGE,
                FRAME_MAX_EDGE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        frame = frame.convertToFormat(QImage.Format.Format_RGBA8888)
        byte_count = frame.sizeInBytes()
        if byte_count <= 0 or byte_count > self.capacity:
            return None
        payload = bytes(frame.constBits())
        if len(payload) != byte_count:
            return None
        self.mapping[:byte_count] = payload
        self.sequence += 1
        return {
            "type": "frame",
            "sequence": self.sequence,
            "width": frame.width(),
            "height": frame.height(),
            "bytesPerLine": frame.bytesPerLine(),
            "byteCount": byte_count,
            "timestampMs": (
                int(timestamp_ms) if timestamp_ms is not None else None
            ),
        }

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.mapping.close()
        self.file.close()
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass


class MappedFrameReader:
    def __init__(self, path, capacity=FRAME_CAPACITY):
        self.path = str(path)
        self.capacity = capacity
        self.file = open(self.path, "rb", buffering=0)
        self.mapping = mmap.mmap(
            self.file.fileno(),
            capacity,
            access=mmap.ACCESS_READ,
        )
        self.last_sequence = 0
        self.closed = False

    def read(self, metadata):
        try:
            sequence = int(metadata["sequence"])
            width = int(metadata["width"])
            height = int(metadata["height"])
            bytes_per_line = int(metadata["bytesPerLine"])
            byte_count = int(metadata["byteCount"])
            timestamp_ms = metadata.get("timestampMs")
            if timestamp_ms is not None:
                timestamp_ms = int(timestamp_ms)
        except (KeyError, TypeError, ValueError, OverflowError):
            return None
        if sequence <= self.last_sequence:
            return None
        if width <= 0 or height <= 0:
            return None
        if bytes_per_line != width * 4:
            return None
        if byte_count != bytes_per_line * height:
            return None
        if byte_count <= 0 or byte_count > self.capacity:
            return None
        payload = bytes(self.mapping[:byte_count])
        if len(payload) != byte_count:
            return None
        image = QImage(
            payload,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGBA8888,
        ).copy()
        if image.isNull():
            return None
        self.last_sequence = sequence
        return image, timestamp_ms

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.mapping.close()
        self.file.close()
