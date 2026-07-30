import ctypes
from ctypes import wintypes

from app.platforms.key_injection import KeyInjectionError


INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("ii",)
    _fields_ = [("type", wintypes.DWORD), ("ii", _INPUTUNION)]


_SCANCODES = {
    "a": (0x1E, False),
    "b": (0x30, False),
    "c": (0x2E, False),
    "d": (0x20, False),
    "e": (0x12, False),
    "f": (0x21, False),
    "g": (0x22, False),
    "h": (0x23, False),
    "i": (0x17, False),
    "j": (0x24, False),
    "k": (0x25, False),
    "l": (0x26, False),
    "m": (0x32, False),
    "n": (0x31, False),
    "o": (0x18, False),
    "p": (0x19, False),
    "q": (0x10, False),
    "r": (0x13, False),
    "s": (0x1F, False),
    "t": (0x14, False),
    "u": (0x16, False),
    "v": (0x2F, False),
    "w": (0x11, False),
    "x": (0x2D, False),
    "y": (0x15, False),
    "z": (0x2C, False),
    "0": (0x0B, False),
    "1": (0x02, False),
    "2": (0x03, False),
    "3": (0x04, False),
    "4": (0x05, False),
    "5": (0x06, False),
    "6": (0x07, False),
    "7": (0x08, False),
    "8": (0x09, False),
    "9": (0x0A, False),
    "up": (0x48, True),
    "down": (0x50, True),
    "left": (0x4B, True),
    "right": (0x4D, True),
    "space": (0x39, False),
    "shift": (0x2A, False),
    "ctrl": (0x1D, False),
    "alt": (0x38, False),
    "enter": (0x1C, False),
    "tab": (0x0F, False),
    "esc": (0x01, False),
    "backspace": (0x0E, False),
    "delete": (0x53, True),
    "cmd": (0x5B, True),
    "home": (0x47, True),
    "end": (0x4F, True),
    "insert": (0x52, True),
    "page_up": (0x49, True),
    "page_down": (0x51, True),
    "caps_lock": (0x3A, False),
    "f1": (0x3B, False),
    "f2": (0x3C, False),
    "f3": (0x3D, False),
    "f4": (0x3E, False),
    "f5": (0x3F, False),
    "f6": (0x40, False),
    "f7": (0x41, False),
    "f8": (0x42, False),
    "f9": (0x43, False),
    "f10": (0x44, False),
    "f11": (0x57, False),
    "f12": (0x58, False),
    "f13": (0x64, False),
    "f14": (0x65, False),
    "f15": (0x66, False),
    "f16": (0x67, False),
    "f17": (0x68, False),
    "f18": (0x69, False),
    "f19": (0x6A, False),
    "f20": (0x6B, False),
}


class WindowsKeyboardBackend:
    def __init__(self, user32=None) -> None:
        self.user32 = user32 or ctypes.WinDLL("user32", use_last_error=True)

    def resolve(self, canonical_name: str) -> tuple[int, bool]:
        scan_code = _SCANCODES.get(canonical_name)
        if scan_code is None:
            raise KeyInjectionError(f"Unsupported key binding: {canonical_name}")
        return scan_code

    def press(self, key: tuple[int, bool]) -> None:
        self._send(key, False)

    def release(self, key: tuple[int, bool]) -> None:
        self._send(key, True)

    def _send(self, key: tuple[int, bool], released: bool) -> None:
        scan_code, extended = key
        flags = KEYEVENTF_SCANCODE
        if extended:
            flags |= KEYEVENTF_EXTENDEDKEY
        if released:
            flags |= KEYEVENTF_KEYUP
        event = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=0,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            ),
        )
        sent = self.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if sent == 1:
            return
        error_code = getattr(ctypes, "get_last_error", lambda: 0)()
        raise KeyInjectionError(
            f"Windows could not send the key input (error {error_code})."
        )
