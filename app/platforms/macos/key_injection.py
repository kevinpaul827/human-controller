"""macos/key_injection.py

Resolve macOS keybinds and post keyboard events.
"""
from app.platforms.key_injection import KeyInjectionError


class MacOSKeyboardBackend:
    _SPECIAL_KEYCODES = {
        "up": 0x7E,
        "down": 0x7D,
        "left": 0x7B,
        "right": 0x7C,
        "space": 0x31,
        "shift": 0x38,
        "ctrl": 0x3B,
        "alt": 0x3A,
        "enter": 0x24,
        "tab": 0x30,
        "esc": 0x35,
        "backspace": 0x33,
        "delete": 0x75,
        "cmd": 0x37,
        "home": 0x73,
        "end": 0x77,
        "insert": 0x72,
        "page_up": 0x74,
        "page_down": 0x79,
        "caps_lock": 0x39,
        "f1": 0x7A,
        "f2": 0x78,
        "f3": 0x63,
        "f4": 0x76,
        "f5": 0x60,
        "f6": 0x61,
        "f7": 0x62,
        "f8": 0x64,
        "f9": 0x65,
        "f10": 0x6D,
        "f11": 0x67,
        "f12": 0x6F,
        "f13": 0x69,
        "f14": 0x6B,
        "f15": 0x71,
        "f16": 0x6A,
        "f17": 0x40,
        "f18": 0x4F,
        "f19": 0x50,
        "f20": 0x5A,
    }

    def __init__(self, quartz=None, character_keycodes=None) -> None:
        if quartz is None:
            import Quartz as quartz_module

            quartz = quartz_module
        if character_keycodes is None:
            from pynput._util.darwin import get_unicode_to_keycode_map

            character_keycodes = get_unicode_to_keycode_map()

        self.quartz = quartz
        self.character_keycodes = character_keycodes
        self.source = quartz.CGEventSourceCreate(
            quartz.kCGEventSourceStateHIDSystemState
        )
        if self.source is None:
            raise RuntimeError("macOS could not create a HID keyboard event source.")
        quartz.CGEventSourceSetLocalEventsSuppressionInterval(self.source, 0.0)
        self._access_requested = False

    def resolve(self, canonical_name: str) -> int:
        special = self._SPECIAL_KEYCODES.get(canonical_name)
        if special is not None:
            return special
        if len(canonical_name) == 1:
            keycode = self.character_keycodes.get(canonical_name)
            if keycode is not None:
                return int(keycode)
        raise KeyInjectionError(f"Unsupported key binding: {canonical_name}")

    def press(self, keycode: int) -> None:
        self._post(keycode, True)

    def release(self, keycode: int) -> None:
        self._post(keycode, False)

    def _post(self, keycode: int, is_pressed: bool) -> None:
        self._ensure_post_access()
        event = self.quartz.CGEventCreateKeyboardEvent(
            self.source, keycode, is_pressed
        )
        if event is None:
            raise RuntimeError("macOS could not create a keyboard event.")
        self.quartz.CGEventSetIntegerValueField(
            event,
            self.quartz.kCGKeyboardEventAutorepeat,
            0,
        )
        self.quartz.CGEventPost(self.quartz.kCGHIDEventTap, event)

    def _ensure_post_access(self) -> None:
        preflight = getattr(self.quartz, "CGPreflightPostEventAccess", None)
        if preflight is None or preflight():
            return
        request = getattr(self.quartz, "CGRequestPostEventAccess", None)
        if request is not None and not self._access_requested:
            self._access_requested = True
            if request():
                return
        raise KeyInjectionError(
            "macOS is blocking keyboard controls. Remove and re-add Human Controller "
            "in System Settings > Privacy & Security > Accessibility, then restart it."
        )
