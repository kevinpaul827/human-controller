from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


BridgeStateValue = Literal["idle", "live", "error"]
KeyActionValue = Literal["press", "release", "reset"]
CapturePhaseValue = Literal["idle", "countdown", "waiting", "recording", "captured"]


class SessionStatusPayload(TypedDict):
    state: BridgeStateValue
    message: NotRequired[str]


class CalibrateStatusPayload(TypedDict):
    state: BridgeStateValue
    message: NotRequired[str]


class GestureMatchPayload(TypedDict):
    gestureId: str | None
    name: str | None
    score: float
    timestamp: float | None
    matched: bool
    hasTemplates: bool
    gestureType: str | None
    threshold: NotRequired[float]
    triggered: NotRequired[bool]
    key: NotRequired[str | None]
    injectionError: NotRequired[str]
    keyAction: NotRequired[KeyActionValue]


class CalibrationUpdatePayload(TypedDict):
    repCount: int
    capturing: bool
    phase: CapturePhaseValue
    countdownRemaining: float


class PosePayload(TypedDict):
    detected: bool
    landmarks: Any
    visibility: Any
    timestampMs: int
    renderJoints: NotRequired[list[str]]
