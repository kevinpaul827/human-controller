from typing import Protocol


class KeyInjectionError(RuntimeError):
    pass


class KeyboardBackend(Protocol):
    def resolve(self, canonical_name: str): ...

    def press(self, key) -> None: ...

    def release(self, key) -> None: ...
