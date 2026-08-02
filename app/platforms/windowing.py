import sys


def configure_overlay_window(window) -> bool:
    if sys.platform != "darwin":
        return False

    from PySide6.QtGui import QGuiApplication

    if QGuiApplication.platformName() in {"minimal", "offscreen"}:
        return False

    from .macos.windowing import configure_overlay_window as configure_macos_overlay

    return configure_macos_overlay(window)


def set_overlay_activation_policy(enabled: bool) -> bool:
    if sys.platform != "darwin":
        return False

    from PySide6.QtGui import QGuiApplication

    if QGuiApplication.platformName() in {"minimal", "offscreen"}:
        return False

    from .macos.windowing import (
        set_overlay_activation_policy as set_macos_policy,
    )

    return set_macos_policy(enabled)
