import unittest

from PySide6.QtWidgets import QApplication

from app.core.camera_session import CameraSession


class CameraSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_stop_deactivates_and_emits_the_owning_bridge(self):
        session = CameraSession()
        stopped = []
        session.cameraStarted.connect(lambda bridge: None)
        session.cameraStopped.connect(stopped.append)
        session.active_bridge = "session"
        session._active = True

        session.stop()

        self.assertFalse(session.active)
        self.assertIsNone(session.active_bridge)
        self.assertEqual(stopped, ["session"])

    def test_error_deactivates_without_emitting_a_normal_stop(self):
        session = CameraSession()
        stopped = []
        errors = []
        session.cameraStopped.connect(stopped.append)
        session.errorOccurred.connect(lambda message, bridge: errors.append((message, bridge)))
        session.active_bridge = "calibrate"
        session._active = True

        session.emit_camera_error("camera failed")

        self.assertFalse(session.active)
        self.assertIsNone(session.active_bridge)
        self.assertEqual(stopped, [])
        self.assertEqual(errors, [("camera failed", "calibrate")])


if __name__ == "__main__":
    unittest.main()
