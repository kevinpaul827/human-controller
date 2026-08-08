import unittest

from app.bridges.session_bridge import SessionBridge, SessionState


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
        self.visible = False
        self.show_count = 0
        self.hide_count = 0
        self.clear_count = 0

    def show_overlay(self) -> None:
        self.visible = True
        self.show_count += 1

    def hide_overlay(self) -> None:
        self.visible = False
        self.hide_count += 1

    def clear(self) -> None:
        self.clear_count += 1


class SessionOverlayVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.camera = FakeCamera()
        self.bridge = SessionBridge(self.camera)
        self.window = FakeOverlayWindow()
        self.bridge.attach_picture_in_picture(self.window)
        self.bridge.state = SessionState.LIVE

    def test_overlay_follows_live_session_camera_ownership(self) -> None:
        self.bridge.apply_overlay_visibility()
        self.assertTrue(self.window.visible)

        self.camera.active_bridge = "calibrate"
        self.bridge.apply_overlay_visibility()

        self.assertFalse(self.window.visible)

        self.camera.active_bridge = "session"
        self.bridge.apply_overlay_visibility()

        self.assertTrue(self.window.visible)
        self.assertEqual(self.window.show_count, 2)

    def test_idle_and_error_states_hide_overlay(self) -> None:
        self.bridge.apply_overlay_visibility()
        self.assertTrue(self.window.visible)

        self.bridge.state = SessionState.IDLE
        self.bridge.apply_overlay_visibility()
        self.assertFalse(self.window.visible)

        self.bridge.state = SessionState.ERROR
        self.bridge.apply_overlay_visibility()
        self.assertFalse(self.window.visible)

    def test_manual_visibility_api_is_not_exposed(self) -> None:
        self.assertFalse(hasattr(self.bridge, "setOverlayVisible"))
        self.assertFalse(hasattr(self.bridge, "getOverlayVisible"))

    def test_camera_start_and_stop_control_overlay_automatically(self) -> None:
        self.bridge.state = SessionState.IDLE

        self.bridge.handle_camera_started("session")
        self.assertEqual(self.bridge.state, SessionState.LIVE)
        self.assertTrue(self.window.visible)

        self.bridge.handle_camera_stopped("session")
        self.assertEqual(self.bridge.state, SessionState.IDLE)
        self.assertFalse(self.window.visible)
        self.assertEqual(self.window.clear_count, 1)


if __name__ == "__main__":
    unittest.main()
