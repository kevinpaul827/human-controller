from __future__ import annotations

import sys

from app.utils.logging_utils import log_debug, log_info


def set_overlay_activation_policy(enabled: bool, appkit=None) -> bool:
    if sys.platform != "darwin":
        return False

    policy_name = "accessory" if enabled else "regular"
    try:
        if appkit is None:
            import AppKit as appkit_module

            appkit = appkit_module

        native_application = appkit.NSApplication.sharedApplication()
        requested_policy = (
            appkit.NSApplicationActivationPolicyAccessory
            if enabled
            else appkit.NSApplicationActivationPolicyRegular
        )
        current_policy = native_application.activationPolicy()
        if current_policy == requested_policy:
            return True

        configured = bool(
            native_application.setActivationPolicy_(requested_policy)
        )
    except Exception as error:
        log_info(
            f"[macos] failed to enable {policy_name} activation policy: "
            f"{error!r}"
        )
        return False

    if not configured:
        log_info(f"[macos] {policy_name} activation policy was rejected")
    return configured


def configure_overlay_window(qt_window) -> bool:
    from PySide6.QtCore import Qt

    qt_window.setAttribute(
        Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow,
        True,
    )
    return configure_fullscreen_overlay(qt_window)


def _overlay_window_level(appkit) -> int:
    screen_saver_level = getattr(appkit, "NSScreenSaverWindowLevel", None)
    if screen_saver_level is not None:
        return int(screen_saver_level)
    return int(getattr(appkit, "NSFloatingWindowLevel", 3))


def configure_fullscreen_overlay(qt_window, appkit=None, objc_module=None) -> bool:
    if sys.platform != "darwin":
        return False

    try:
        if appkit is None:
            import AppKit as appkit_module

            appkit = appkit_module
        if objc_module is None:
            import objc as imported_objc

            objc_module = imported_objc

        native_view = objc_module.objc_object(c_void_p=int(qt_window.winId()))
        native_window = native_view.window()
        if native_window is None:
            return False

        nonactivating_panel = getattr(
            appkit, "NSWindowStyleMaskNonactivatingPanel", None
        )
        style_mask = getattr(native_window, "styleMask", None)
        set_style_mask = getattr(native_window, "setStyleMask_", None)
        if (
            nonactivating_panel is not None
            and callable(style_mask)
            and callable(set_style_mask)
        ):
            set_style_mask(int(style_mask()) | int(nonactivating_panel))

        behavior = int(native_window.collectionBehavior())
        behavior &= ~int(
            getattr(appkit, "NSWindowCollectionBehaviorMoveToActiveSpace", 0)
        )
        behavior |= int(appkit.NSWindowCollectionBehaviorCanJoinAllSpaces)
        behavior |= int(appkit.NSWindowCollectionBehaviorIgnoresCycle)
        behavior |= int(
            getattr(appkit, "NSWindowCollectionBehaviorStationary", 0)
        )

        join_all_apps = getattr(
            appkit, "NSWindowCollectionBehaviorCanJoinAllApplications", None
        )
        if join_all_apps is not None:
            behavior &= ~int(
                getattr(appkit, "NSWindowCollectionBehaviorPrimary", 0)
                | getattr(appkit, "NSWindowCollectionBehaviorAuxiliary", 0)
            )
            behavior |= int(join_all_apps)

        behavior &= ~int(
            getattr(appkit, "NSWindowCollectionBehaviorFullScreenPrimary", 0)
            | getattr(appkit, "NSWindowCollectionBehaviorFullScreenNone", 0)
        )
        behavior |= int(appkit.NSWindowCollectionBehaviorFullScreenAuxiliary)

        native_window.setCollectionBehavior_(behavior)
        existing_level = int(native_window.level())
        if hasattr(native_window, "setFloatingPanel_"):
            native_window.setFloatingPanel_(True)
        native_window.setLevel_(
            max(existing_level, _overlay_window_level(appkit))
        )
        native_window.setHidesOnDeactivate_(False)
        order_front_regardless = getattr(
            native_window, "orderFrontRegardless", None
        )
        if callable(order_front_regardless):
            order_front_regardless()
        else:
            order_front = getattr(native_window, "orderFront_", None)
            if callable(order_front):
                order_front(None)
        native_class = (
            str(native_window.className())
            if hasattr(native_window, "className")
            else type(native_window).__name__
        )
        log_debug(
            f"[overlay] configured {native_class}: "
            f"behavior={behavior:#x}, level={int(native_window.level())}"
        )
        return True
    except Exception as error:
        log_debug(f"[overlay] native full-screen configuration failed: {error!r}")
        return False
