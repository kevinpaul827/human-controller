import unittest

from app.session_bridge import SessionBridge, SessionState


class FakeSignal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)

    def emit(self, *args) -> None:
        for callback in self.callbacks:
            callback(*args)


class FakeCamera:
    def __init__(self) -> None:
        self.cameraStarted = FakeSignal()
        self.cameraStopped = FakeSignal()
        self.errorOccurred = FakeSignal()
        self.previewFrameReady = FakeSignal()
        self.frameProcessed = FakeSignal()
        self.gestureMatchUpdated = FakeSignal()
        self.previewAspectRatioChanged = FakeSignal()
        self.active_bridge = "session"


class FakeOverlayWindow:
    def __init__(self) -> None:
        self.visibilityChanged = FakeSignal()
        self.visible = False
        self.show_count = 0
        self.hide_count = 0

    def show_overlay(self) -> None:
        self.visible = True
        self.show_count += 1
        self.visibilityChanged.emit(True)

    def hide_overlay(self) -> None:
        self.visible = False
        self.hide_count += 1
        self.visibilityChanged.emit(False)

    def isVisible(self) -> bool:
        return self.visible


class SessionOverlayVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.camera = FakeCamera()
        self.bridge = SessionBridge(self.camera)
        self.window = FakeOverlayWindow()
        self.bridge.attach_picture_in_picture(self.window)
        self.bridge.state = SessionState.LIVE

    def test_temporary_ownership_loss_does_not_erase_overlay_request(self) -> None:
        self.bridge.apply_overlay_visibility()
        self.assertTrue(self.window.visible)

        self.camera.active_bridge = "calibrate"
        self.bridge.apply_overlay_visibility()

        self.assertFalse(self.window.visible)
        self.assertTrue(self.bridge.overlay_requested)

        self.camera.active_bridge = "session"
        self.bridge.apply_overlay_visibility()

        self.assertTrue(self.window.visible)
        self.assertEqual(self.window.show_count, 2)

    def test_direct_window_close_updates_overlay_request(self) -> None:
        self.bridge.apply_overlay_visibility()

        self.window.hide_overlay()

        self.assertFalse(self.window.visible)
        self.assertFalse(self.bridge.overlay_requested)


if __name__ == "__main__":
    unittest.main()
