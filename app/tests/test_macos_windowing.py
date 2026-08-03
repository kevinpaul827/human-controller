import unittest
from unittest.mock import MagicMock, patch

from app.platforms.macos.windowing import (
    configure_fullscreen_overlay,
    set_overlay_activation_policy as set_macos_overlay_activation_policy,
)
from app.platforms.windowing import configure_overlay_window


class FakeQtWindow:
    def winId(self):
        return 1234


class FakeNativeWindow:
    def __init__(self, behavior=0, style_mask=0):
        self.behavior = behavior
        self.style_mask = style_mask
        self.level_value = 0
        self.hides_on_deactivate = None
        self.floating_panel = False
        self.ordered_front_regardless = False

    def collectionBehavior(self):
        return self.behavior

    def level(self):
        return self.level_value

    def setCollectionBehavior_(self, behavior):
        self.behavior = behavior

    def styleMask(self):
        return self.style_mask

    def setStyleMask_(self, style_mask):
        self.style_mask = style_mask

    def setLevel_(self, level):
        self.level_value = level

    def setHidesOnDeactivate_(self, value):
        self.hides_on_deactivate = value

    def setFloatingPanel_(self, value):
        self.floating_panel = value

    def orderFrontRegardless(self):
        self.ordered_front_regardless = True


class LegacyNativeWindow:
    def __init__(self):
        self.behavior = 0
        self.level_value = 0
        self.hides_on_deactivate = None
        self.ordered_front_sender = object()

    def collectionBehavior(self):
        return self.behavior

    def setCollectionBehavior_(self, behavior):
        self.behavior = behavior

    def level(self):
        return self.level_value

    def setLevel_(self, level):
        self.level_value = level

    def setHidesOnDeactivate_(self, value):
        self.hides_on_deactivate = value

    def orderFront_(self, sender):
        self.ordered_front_sender = sender


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
    NSWindowCollectionBehaviorStationary = 16
    NSWindowCollectionBehaviorIgnoresCycle = 64
    NSWindowCollectionBehaviorFullScreenAuxiliary = 256
    NSWindowCollectionBehaviorFullScreenPrimary = 128
    NSWindowCollectionBehaviorFullScreenNone = 512
    NSWindowCollectionBehaviorPrimary = 65536
    NSWindowCollectionBehaviorAuxiliary = 131072
    NSWindowCollectionBehaviorCanJoinAllApplications = 262144
    NSFloatingWindowLevel = 3
    NSScreenSaverWindowLevel = 1000
    NSWindowStyleMaskNonactivatingPanel = 128


class LegacyAppKit:
    NSWindowCollectionBehaviorCanJoinAllSpaces = 1
    NSWindowCollectionBehaviorMoveToActiveSpace = 2
    NSWindowCollectionBehaviorIgnoresCycle = 64
    NSWindowCollectionBehaviorFullScreenAuxiliary = 256
    NSFloatingWindowLevel = 3


class MacOSWindowingTests(unittest.TestCase):
    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    def test_overlay_policy_switches_to_accessory(self):
        appkit = MagicMock()
        appkit.NSApplicationActivationPolicyRegular = 0
        appkit.NSApplicationActivationPolicyAccessory = 1
        native_application = appkit.NSApplication.sharedApplication.return_value
        native_application.activationPolicy.return_value = 0
        native_application.setActivationPolicy_.return_value = True

        self.assertTrue(set_macos_overlay_activation_policy(True, appkit))

        native_application.setActivationPolicy_.assert_called_once_with(1)

    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    def test_overlay_policy_restores_regular_mode(self):
        appkit = MagicMock()
        appkit.NSApplicationActivationPolicyRegular = 0
        appkit.NSApplicationActivationPolicyAccessory = 1
        native_application = appkit.NSApplication.sharedApplication.return_value
        native_application.activationPolicy.return_value = 1
        native_application.setActivationPolicy_.return_value = True

        self.assertTrue(set_macos_overlay_activation_policy(False, appkit))

        native_application.setActivationPolicy_.assert_called_once_with(0)

    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    def test_overlay_policy_is_idempotent(self):
        appkit = MagicMock()
        appkit.NSApplicationActivationPolicyRegular = 0
        appkit.NSApplicationActivationPolicyAccessory = 1
        native_application = appkit.NSApplication.sharedApplication.return_value
        native_application.activationPolicy.return_value = 1

        self.assertTrue(set_macos_overlay_activation_policy(True, appkit))

        native_application.setActivationPolicy_.assert_not_called()

    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    @patch("app.platforms.macos.windowing.log_info")
    def test_overlay_policy_rejection_is_visible(self, log_info):
        appkit = MagicMock()
        appkit.NSApplicationActivationPolicyRegular = 0
        appkit.NSApplicationActivationPolicyAccessory = 1
        native_application = appkit.NSApplication.sharedApplication.return_value
        native_application.activationPolicy.return_value = 0
        native_application.setActivationPolicy_.return_value = False

        self.assertFalse(set_macos_overlay_activation_policy(True, appkit))

        log_info.assert_called_once_with(
            "[macos] accessory activation policy was rejected"
        )

    @patch("app.platforms.macos.windowing.sys.platform", "linux")
    def test_overlay_policy_is_unchanged_off_macos(self):
        appkit = MagicMock()

        self.assertFalse(set_macos_overlay_activation_policy(True, appkit))

        appkit.NSApplication.sharedApplication.assert_not_called()

    @patch("app.platforms.windowing.sys.platform", "darwin")
    @patch("PySide6.QtGui.QGuiApplication.platformName", return_value="offscreen")
    def test_offscreen_qt_platform_skips_native_window_configuration(
        self, _platform_name
    ):
        self.assertFalse(configure_overlay_window(FakeQtWindow()))

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
        self.assertTrue(
            window.behavior
            & ModernAppKit.NSWindowCollectionBehaviorStationary
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
            window.level_value, ModernAppKit.NSScreenSaverWindowLevel
        )
        self.assertTrue(
            window.style_mask & ModernAppKit.NSWindowStyleMaskNonactivatingPanel
        )
        self.assertTrue(window.floating_panel)
        self.assertFalse(window.hides_on_deactivate)
        self.assertTrue(window.ordered_front_regardless)

    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    def test_existing_higher_level_is_preserved(self):
        window = FakeNativeWindow()
        window.level_value = ModernAppKit.NSScreenSaverWindowLevel + 5

        configure_fullscreen_overlay(FakeQtWindow(), ModernAppKit, FakeObjC(window))

        self.assertEqual(
            window.level_value, ModernAppKit.NSScreenSaverWindowLevel + 5
        )

    @patch("app.platforms.macos.windowing.sys.platform", "darwin")
    def test_legacy_overlay_uses_available_fallbacks(self):
        window = LegacyNativeWindow()

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
        self.assertEqual(window.level_value, LegacyAppKit.NSFloatingWindowLevel)
        self.assertFalse(window.hides_on_deactivate)
        self.assertIsNone(window.ordered_front_sender)

    @patch("app.platforms.macos.windowing.sys.platform", "linux")
    def test_non_macos_is_noop(self):
        self.assertFalse(
            configure_fullscreen_overlay(
                FakeQtWindow(), ModernAppKit, FakeObjC(FakeNativeWindow())
            )
        )


if __name__ == "__main__":
    unittest.main()
