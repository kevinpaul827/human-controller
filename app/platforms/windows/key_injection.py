import ctypes
from ctypes import wintypes

from app.platforms.key_injection import KeyInjectionError
from pynput.keyboard import Controller, Key


_KEYS = {
    "a": "a",
    "b": "b",
    "c": "c",
    "d": "d",
    "e": "e",
    "f": "f",
    "g": "g",
    "h": "h",
    "i": "i",
    "j": "j",
    "k": "k",
    "l": "l",
    "m": "m",
    "n": "n",
    "o": "o",
    "p": "p",
    "q": "q",
    "r": "r",
    "s": "s",
    "t": "t",
    "u": "u",
    "v": "v",
    "w": "w",
    "x": "x",
    "y": "y",
    "z": "z",
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "space": Key.space,
    "shift": Key.shift,
    "ctrl": Key.ctrl,
    "alt": Key.alt,
    "enter": Key.enter,
    "tab": Key.tab,
    "esc": Key.esc,
    "backspace": Key.backspace,
    "delete": Key.delete,
    "cmd": Key.cmd,
    "home": Key.home,
    "end": Key.end,
    "insert": Key.insert,
    "page_up": Key.page_up,
    "page_down": Key.page_down,
    "caps_lock": Key.caps_lock,
    "f1": Key.f1,
    "f2": Key.f2,
    "f3": Key.f3,
    "f4": Key.f4,
    "f5": Key.f5,
    "f6": Key.f6,
    "f7": Key.f7,
    "f8": Key.f8,
    "f9": Key.f9,
    "f10": Key.f10,
    "f11": Key.f11,
    "f12": Key.f12,
    "f13": Key.f13,
    "f14": Key.f14,
    "f15": Key.f15,
    "f16": Key.f16,
    "f17": Key.f17,
    "f18": Key.f18,
    "f19": Key.f19,
    "f20": Key.f20,
}


class WindowsKeyboardBackend:
    def __init__(self, user32=None) -> None:
        self.user32 = user32 or ctypes.WinDLL("user32", use_last_error=True)
        self.keyboard = Controller()

    def resolve(self, canonical_name: str) -> tuple[int, bool]:
        key = _KEYS.get(canonical_name)
        if key is None:
            raise KeyInjectionError(f"Unsupported key binding: {canonical_name}")
        return key

    def press(self, key: tuple[int, bool]) -> None:
        self.keyboard.press(key)

    def release(self, key: tuple[int, bool]) -> None:
        self.keyboard.release(key)
