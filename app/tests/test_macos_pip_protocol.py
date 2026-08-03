import os
import unittest

from PySide6.QtGui import QColor, QImage

from app.platforms.macos.pip_protocol import (
    MappedFrameReader,
    MappedFrameWriter,
    MessageBuffer,
    encode_message,
)


class PipMessageProtocolTests(unittest.TestCase):
    def test_fragmented_and_coalesced_messages_are_decoded(self):
        parser = MessageBuffer()
        first = encode_message({"type": "show"})
        second = encode_message({"type": "hide"})

        self.assertEqual(parser.feed(first[:5]), [])
        self.assertEqual(
            parser.feed(first[5:] + b"ordinary log output\n" + second),
            [{"type": "show"}, {"type": "hide"}],
        )

    def test_invalid_json_is_ignored(self):
        parser = MessageBuffer()

        self.assertEqual(parser.feed(b"HC_PIP:{invalid}\n"), [])


class PipMappedFrameTests(unittest.TestCase):
    def setUp(self):
        self.writer = MappedFrameWriter(capacity=4096)
        self.reader = MappedFrameReader(self.writer.path, capacity=4096)

    def tearDown(self):
        self.reader.close()
        path = self.writer.path
        self.writer.close()
        self.assertFalse(os.path.exists(path))

    def test_odd_width_rgb_frame_round_trips_and_detaches(self):
        image = QImage(3, 2, QImage.Format.Format_RGB888)
        image.fill(QColor("#123456"))
        metadata = self.writer.write(image, 42)

        decoded, timestamp_ms = self.reader.read(metadata)
        replacement = QImage(3, 2, QImage.Format.Format_RGB888)
        replacement.fill(QColor("#abcdef"))
        self.writer.write(replacement, 43)

        self.assertEqual(decoded.size(), image.size())
        self.assertEqual(decoded.pixelColor(2, 1), QColor("#123456"))
        self.assertEqual(timestamp_ms, 42)

    def test_stale_sequence_is_ignored(self):
        image = QImage(2, 2, QImage.Format.Format_RGBA8888)
        image.fill(QColor("red"))
        metadata = self.writer.write(image, 1)

        self.assertIsNotNone(self.reader.read(metadata))
        self.assertIsNone(self.reader.read(metadata))

    def test_malformed_metadata_is_rejected(self):
        self.assertIsNone(self.reader.read({"type": "frame"}))
        self.assertIsNone(
            self.reader.read(
                {
                    "sequence": 1,
                    "width": 100,
                    "height": 100,
                    "bytesPerLine": 400,
                    "byteCount": 999999,
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
