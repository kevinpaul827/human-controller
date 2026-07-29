from __future__ import annotations

import time

from .platforms import create_keyboard_backend
from .platforms.key_injection import KeyInjectionError


DEFAULT_KEY_PRESS_SECONDS = 0.12

_ALIASES = {
    "arrowup": "up",
    "arrowdown": "down",
    "arrowleft": "left",
    "arrowright": "right",
    "control": "ctrl",
    "option": "alt",
    "return": "enter",
    "escape": "esc",
    "meta": "cmd",
    "command": "cmd",
    "pageup": "page_up",
    "pagedown": "page_down",
    "capslock": "caps_lock",
}


class KeyInjector:
    def __init__(
        self,
        press_duration_seconds: float = DEFAULT_KEY_PRESS_SECONDS,
        sleeper=time.sleep,
        backend=None,
    ) -> None:
        self.press_duration_seconds = max(0.0, float(press_duration_seconds))
        self._sleeper = sleeper
        self._backend = backend
        self._held_keys: dict[str, object] = {}

    def _ensure_backend(self):
        if self._backend is None:
            self._backend = create_keyboard_backend()

    @staticmethod
    def canonical_name(key_name: str) -> str:
        resolved = str(key_name or "").strip().lower()
        if not resolved:
            raise KeyInjectionError("A key binding cannot be empty.")
        return _ALIASES.get(resolved, resolved)

    def resolve(self, key_name: str):
        canonical = self.canonical_name(key_name)
        self._ensure_backend()
        return self._backend.resolve(canonical)

    def press(self, key_name: str) -> bool:
        canonical = self.canonical_name(key_name)
        if canonical in self._held_keys:
            return False
        self._ensure_backend()
        key = self._backend.resolve(canonical)
        try:
            self._backend.press(key)
        except KeyInjectionError:
            raise
        except Exception as error:
            raise self._injection_error() from error
        self._held_keys[canonical] = key
        return True

    def release(self, key_name: str) -> bool:
        canonical = self.canonical_name(key_name)
        key = self._held_keys.get(canonical)
        if key is None:
            return False
        try:
            self._backend.release(key)
        except KeyInjectionError:
            raise
        except Exception as error:
            raise self._injection_error() from error
        del self._held_keys[canonical]
        return True

    def release_all(self) -> None:
        first_error = None
        for canonical, key in list(self._held_keys.items()):
            try:
                self._backend.release(key)
                del self._held_keys[canonical]
            except Exception as error:
                first_error = first_error or error
        if first_error is not None:
            raise self._injection_error() from first_error

    def press_and_release(self, key_name: str) -> None:
        if not self.press(key_name):
            return
        try:
            self._sleeper(self.press_duration_seconds)
        finally:
            self.release(key_name)

    @staticmethod
    def _injection_error() -> KeyInjectionError:
        return KeyInjectionError(
            "The key could not be sent. Check the app's Accessibility permission."
        )
