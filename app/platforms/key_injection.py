"""platforms/key_injection.py

Interface to define keyboard backend functions
and key injection error.
"""

from typing import Protocol


class KeyInjectionError(RuntimeError):
    pass


class KeyboardBackend(Protocol):
    def resolve(self, canonical_name: str): ...

    def press(self, key) -> None: ...

    def release(self, key) -> None: ...
