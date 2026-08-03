import os
import unittest

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication

from app.platforms.macos.pip_process import (
    MacOSPictureInPictureProxy,
    MacOSPipProcessTransport,
)
from app.platforms.macos.pip_protocol import PROTOCOL_VERSION, MessageBuffer


class FakeFrameWriter:
    path = "/tmp/human-controller-pose-regression-frame"

    def close(self):
        pass


class FakeProcess:
    def __init__(self):
        self.running = True
        self.writes = []

    def state(self):
        return (
            QProcess.ProcessState.Running
            if self.running
            else QProcess.ProcessState.NotRunning
        )

    def write(self, payload):
        self.writes.append(bytes(payload))
        return len(payload)

    def waitForBytesWritten(self, _timeout_ms):
        return True

    def waitForFinished(self, _timeout_ms):
        self.running = False
        return True


class MacOSPipPoseIpcRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_real_pose_estimator_arrays_cross_the_control_channel(self):
        process = FakeProcess()
        transport = MacOSPipProcessTransport(
            frame_writer=FakeFrameWriter(),
        )
        transport.process = process
        transport.ready = True
        proxy = MacOSPictureInPictureProxy(transport)
        self.addCleanup(proxy.shutdown)
        proxy.show_overlay()
        process.writes.clear()

        pose = {
            "detected": True,
            "landmarks": np.array(
                [[0.1, 0.2, -0.3], [0.4, 0.5, -0.6]],
                dtype=np.float64,
            ),
            "visibility": np.array([0.95, 0.8], dtype=np.float64),
            "timestampMs": 321,
            "renderJoints": ["L_ELBOW"],
        }

        proxy.set_pose(pose)

        messages = MessageBuffer().feed(b"".join(process.writes))
        self.assertEqual(
            messages,
            [
                {
                    "type": "pose",
                    "payload": {
                        "detected": True,
                        "landmarks": [
                            [0.1, 0.2, -0.3],
                            [0.4, 0.5, -0.6],
                        ],
                        "visibility": [0.95, 0.8],
                        "timestampMs": 321,
                        "renderJoints": ["L_ELBOW"],
                    },
                }
            ],
        )

    def test_pose_arrays_cached_before_ready_cross_in_initial_sync(self):
        process = FakeProcess()
        transport = MacOSPipProcessTransport(
            frame_writer=FakeFrameWriter(),
        )
        transport.process = process
        proxy = MacOSPictureInPictureProxy(transport)
        self.addCleanup(proxy.shutdown)
        pose = {
            "detected": True,
            "landmarks": np.array(
                [[0.15, 0.25, -0.35]],
                dtype=np.float64,
            ),
            "visibility": np.array([0.9], dtype=np.float64),
            "timestampMs": 654,
        }

        proxy.set_pose(pose)
        proxy.show_overlay()
        transport._handle_message(
            process,
            transport.generation,
            {"type": "ready", "protocol": PROTOCOL_VERSION},
        )

        messages = MessageBuffer().feed(b"".join(process.writes))
        self.assertEqual(
            messages,
            [
                {
                    "type": "sync",
                    "visible": True,
                    "pose": {
                        "detected": True,
                        "landmarks": [[0.15, 0.25, -0.35]],
                        "visibility": [0.9],
                        "timestampMs": 654,
                    },
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
