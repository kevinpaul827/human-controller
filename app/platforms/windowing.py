import sys


def configure_overlay_window(window) -> bool:
    if sys.platform != "darwin":
        return False

    from .macos.windowing import configure_overlay_window as configure_macos_overlay

    return configure_macos_overlay(window)
