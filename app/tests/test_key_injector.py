import ctypes
import unittest

from app.key_injector import (
    DEFAULT_KEY_PRESS_SECONDS,
    KeyInjectionError,
    KeyInjector,
)
from app.platforms.macos.key_injection import MacOSKeyboardBackend
from app.platforms.windows.key_injection import (
    WindowsKeyboardBackend,
    INPUT,
    KEYEVENTF_EXTENDEDKEY,
    KEYEVENTF_KEYUP,
    KEYEVENTF_SCANCODE
)


class FakeBackend:
    def __init__(self):
        self.events = []

    def resolve(self, canonical_name):
        self.events.append(("resolve", canonical_name))
        return f"resolved:{canonical_name}"

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))


class FakeQuartz:
    kCGEventSourceStateHIDSystemState = 1
    kCGKeyboardEventAutorepeat = 8
    kCGHIDEventTap = 9

    def __init__(self):
        self.calls = []
        self.source = object()
        self.post_access = True

    def CGEventSourceCreate(self, state):
        self.calls.append(("source", state))
        return self.source

    def CGEventSourceSetLocalEventsSuppressionInterval(self, source, seconds):
        self.calls.append(("suppression", source, seconds))

    def CGPreflightPostEventAccess(self):
        self.calls.append(("preflight",))
        return self.post_access

    def CGRequestPostEventAccess(self):
        self.calls.append(("request",))
        return self.post_access

    def CGEventCreateKeyboardEvent(self, source, keycode, is_pressed):
        event = {"source": source, "keycode": keycode, "pressed": is_pressed}
        self.calls.append(("create", source, keycode, is_pressed))
        return event

    def CGEventSetIntegerValueField(self, event, field, value):
        self.calls.append(("field", event, field, value))

    def CGEventPost(self, tap, event):
        self.calls.append(("post", tap, event))


class FakeUser32:
    def __init__(self):
        self.events = []
        self.result = 1

    def SendInput(self, count, event_pointer, structure_size):
        event = ctypes.cast(event_pointer, ctypes.POINTER(INPUT)).contents

        self.events.append(
            (
                count,
                structure_size,
                event.type,
                event.union.ki.wVk,
                event.union.ki.wScan,
                event.union.ki.dwFlags,
            )
        )

        return self.result


class KeyInjectorTests(unittest.TestCase):
    def test_press_stays_down_until_release_and_does_not_repeat(self):
        backend = FakeBackend()
        injector = KeyInjector(backend=backend)

        self.assertTrue(injector.press("W"))
        self.assertFalse(injector.press("w"))
        self.assertTrue(injector.release("w"))

        self.assertEqual(
            backend.events,
            [
                ("resolve", "w"),
                ("press", "resolved:w"),
                ("release", "resolved:w"),
            ],
        )

    def test_release_all_releases_every_held_key(self):
        backend = FakeBackend()
        injector = KeyInjector(backend=backend)
        injector.press("w")
        injector.press("ArrowUp")

        injector.release_all()

        self.assertIn(("release", "resolved:w"), backend.events)
        self.assertIn(("release", "resolved:up"), backend.events)
        self.assertFalse(injector.release("w"))

    def test_press_and_release_remains_available_for_shortcuts(self):
        backend = FakeBackend()
        sleeps = []
        injector = KeyInjector(backend=backend, sleeper=sleeps.append)

        injector.press_and_release("w")

        self.assertEqual(sleeps, [DEFAULT_KEY_PRESS_SECONDS])
        self.assertEqual(
            backend.events,
            [
                ("resolve", "w"),
                ("press", "resolved:w"),
                ("release", "resolved:w"),
            ],
        )

    def test_quartz_backend_posts_hid_keycode_down_and_up_without_autorepeat(self):
        quartz = FakeQuartz()
        backend = MacOSKeyboardBackend(
            quartz=quartz,
            character_keycodes={"w": 13},
        )

        keycode = backend.resolve("w")
        backend.press(keycode)
        backend.release(keycode)

        self.assertEqual(keycode, 13)
        self.assertIn(("source", quartz.kCGEventSourceStateHIDSystemState), quartz.calls)
        self.assertIn(("suppression", quartz.source, 0.0), quartz.calls)
        creates = [call for call in quartz.calls if call[0] == "create"]
        self.assertEqual(
            creates,
            [
                ("create", quartz.source, 13, True),
                ("create", quartz.source, 13, False),
            ],
        )
        posts = [call for call in quartz.calls if call[0] == "post"]
        self.assertEqual([call[1] for call in posts], [9, 9])
        fields = [call for call in quartz.calls if call[0] == "field"]
        self.assertEqual([call[3] for call in fields], [0, 0])

    def test_quartz_backend_requests_access_and_reports_denial(self):
        quartz = FakeQuartz()
        quartz.post_access = False
        backend = MacOSKeyboardBackend(
            quartz=quartz,
            character_keycodes={"w": 13},
        )

        with self.assertRaisesRegex(KeyInjectionError, "Remove and re-add"):
            backend.press(13)
        with self.assertRaises(KeyInjectionError):
            backend.press(13)

        self.assertEqual(quartz.calls.count(("request",)), 1)

    def test_windows_backend_posts_scan_codes_with_extended_and_release_flags(self):
        user32 = FakeUser32()
        backend = WindowsKeyboardBackend(user32=user32)
        token = backend.resolve("left")

        backend.press(token)
        backend.release(token)

        self.assertEqual(
            user32.events,
            [
                (
                    1,
                    ctypes.sizeof(INPUT),
                    1,
                    0,
                    0x4B,
                    KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY,
                ),
                (
                    1,
                    ctypes.sizeof(INPUT),
                    1,
                    0,
                    0x4B,
                    KEYEVENTF_SCANCODE
                    | KEYEVENTF_EXTENDEDKEY
                    | KEYEVENTF_KEYUP,
                ),
            ],
        )

    def test_windows_backend_rejects_unknown_keys_and_reports_send_failure(self):
        user32 = FakeUser32()
        backend = WindowsKeyboardBackend(user32=user32)

        with self.assertRaises(KeyInjectionError):
            backend.resolve("[")

        user32.result = 0
        with self.assertRaisesRegex(KeyInjectionError, "Windows could not send"):
            backend.press(backend.resolve("w"))


if __name__ == "__main__":
    unittest.main()
