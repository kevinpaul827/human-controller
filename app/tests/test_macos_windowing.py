import unittest
from unittest.mock import patch

from app.platforms.macos.windowing import configure_fullscreen_overlay


class FakeQtWindow:
    def winId(self):
        return 1234


class FakeNativeWindow:
    def __init__(self, behavior=0):
        self.behavior = behavior
        self.level_value = 0
        self.hides_on_deactivate = None
        self.floating_panel = False

    def collectionBehavior(self):
        return self.behavior

    def level(self):
        return self.level_value

    def setCollectionBehavior_(self, behavior):
        self.behavior = behavior

    def setLevel_(self, level):
        self.level_value = level

    def setHidesOnDeactivate_(self, value):
        self.hides_on_deactivate = value

    def setFloatingPanel_(self, value):
        self.floating_panel = value


class FakeNativeView:
    def __init__(self, window):
        self.native_window = window

    def window(self):
        return self.native_window


class FakeObjC:
    def __init__(self, window):
        self.native_window = window
        self.pointer = None

    def objc_object(self, *, c_void_p):
        self.pointer = c_void_p
        return FakeNativeView(self.native_window)


class ModernAppKit:
    NSWindowCollectionBehaviorCanJoinAllSpaces = 1
    NSWindowCollectionBehaviorMoveToActiveSpace = 2
    NSWindowCollectionBehaviorIgnoresCycle = 64
    NSWindowCollectionBehaviorFullScreenAuxiliary = 256
    NSWindowCollectionBehaviorFullScreenPrimary = 128
    NSWindowCollectionBehaviorFullScreenNone = 512
    NSWindowCollectionBehaviorPrimary = 65536
    NSWindowCollectionBehaviorAuxiliary = 131072
    NSWindowCollectionBehaviorCanJoinAllApplications = 262144
    NSFloatingWindowLevel = 3
    NSScreenSaverWindowLevel = 1000


class LegacyAppKit:
    NSWindowCollectionBehaviorCanJoinAllSpaces = 1
    NSWindowCollectionBehaviorMoveToActiveSpace = 2
    NSWindowCollectionBehaviorIgnoresCycle = 64
    NSWindowCollectionBehaviorFullScreenAuxiliary = 256
    NSFloatingWindowLevel = 3


class MacOSWindowingTests(unittest.TestCase):
    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    def test_modern_overlay_joins_all_apps_and_spaces(self):
        window = FakeNativeWindow(
            ModernAppKit.NSWindowCollectionBehaviorMoveToActiveSpace
            | ModernAppKit.NSWindowCollectionBehaviorAuxiliary
            | ModernAppKit.NSWindowCollectionBehaviorFullScreenPrimary
            | ModernAppKit.NSWindowCollectionBehaviorFullScreenNone
        )
        objc = FakeObjC(window)

        configured = configure_fullscreen_overlay(
            FakeQtWindow(), ModernAppKit, objc
        )

        self.assertTrue(configured)
        self.assertEqual(objc.pointer, 1234)
        self.assertTrue(
            window.behavior
            & ModernAppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
        )
        self.assertTrue(
            window.behavior
            & ModernAppKit.NSWindowCollectionBehaviorCanJoinAllApplications
        )
        self.assertFalse(
            window.behavior & ModernAppKit.NSWindowCollectionBehaviorAuxiliary
        )
        self.assertFalse(
            window.behavior
            & ModernAppKit.NSWindowCollectionBehaviorMoveToActiveSpace
        )
        self.assertTrue(
            window.behavior
            & ModernAppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        self.assertFalse(
            window.behavior
            & ModernAppKit.NSWindowCollectionBehaviorFullScreenPrimary
        )
        self.assertFalse(
            window.behavior
            & ModernAppKit.NSWindowCollectionBehaviorFullScreenNone
        )
        self.assertEqual(
            window.level_value, ModernAppKit.NSFloatingWindowLevel
        )
        self.assertTrue(window.floating_panel)
        self.assertFalse(window.hides_on_deactivate)

    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    def test_existing_higher_level_is_preserved(self):
        window = FakeNativeWindow()
        window.level_value = ModernAppKit.NSFloatingWindowLevel + 5

        configure_fullscreen_overlay(FakeQtWindow(), ModernAppKit, FakeObjC(window))

        self.assertEqual(
            window.level_value, ModernAppKit.NSFloatingWindowLevel + 5
        )

    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    def test_legacy_overlay_uses_full_screen_auxiliary(self):
        window = FakeNativeWindow()

        self.assertTrue(
            configure_fullscreen_overlay(
                FakeQtWindow(), LegacyAppKit, FakeObjC(window)
            )
        )
        self.assertTrue(
            window.behavior
            & LegacyAppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
        )
        self.assertTrue(
            window.behavior
            & LegacyAppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

    @patch("app.platforms.macos.windowing.sys.platform", "linux")
    def test_non_macos_is_noop(self):
        self.assertFalse(
            configure_fullscreen_overlay(
                FakeQtWindow(), ModernAppKit, FakeObjC(FakeNativeWindow())
            )
        )


if __name__ == "__main__":
    unittest.main()
