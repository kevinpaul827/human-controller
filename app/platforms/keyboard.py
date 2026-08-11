"""keyboard.py

Creates platform-specific keyboard backend for
macOS and Windows.
"""
import sys

from .key_injection import KeyInjectionError


def create_keyboard_backend():
    try:
        if sys.platform == "darwin":
            from .macos.key_injection import MacOSKeyboardBackend

            return MacOSKeyboardBackend()
        if sys.platform == "win32":
            from .windows.key_injection import WindowsKeyboardBackend

            return WindowsKeyboardBackend()
        raise KeyInjectionError("Human Controller supports only macOS and Windows.")
    except KeyInjectionError:
        raise
    except Exception as error:
        raise KeyInjectionError(
            "Keyboard control is unavailable. Check the system accessibility permissions."
        ) from error
