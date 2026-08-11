"""system_settings.py

Open platform privacy and accessibility settings.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def open_camera_settings() -> bool:
    if sys.platform == "win32":
        QDesktopServices.openUrl(QUrl("ms-settings:privacy-webcam"))
        return True

    if sys.platform == "darwin":
        QDesktopServices.openUrl(
            QUrl("x-apple.systempreferences:com.apple.preference.security?Privacy_Camera")
        )
        return True

    return False


def open_accessibility_settings() -> bool:
    if sys.platform == "darwin":
        QDesktopServices.openUrl(
            QUrl(
                "x-apple.systempreferences:com.apple.preference.security?"
                "Privacy_Accessibility"
            )
        )
        return True

    return False
