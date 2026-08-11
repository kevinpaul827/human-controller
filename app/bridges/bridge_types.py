"""bridge_types.py

Typed payload definitions used by bridges to be exposed
to frontend.
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

# Bridge states based on camera.
BridgeStateValue = Literal["idle", "live", "error"]

# Keyboard actions associated with matched gestures.
KeyActionValue = Literal["press", "release", "reset"]

# Stages used during gesture calibration.
CapturePhaseValue = Literal["idle", "countdown", "waiting", "recording", "captured"]


class SessionStatusPayload(TypedDict):
    """Status update emitted by session bridge."""
    state: BridgeStateValue
    message: NotRequired[str]


class CalibrateStatusPayload(TypedDict):
    """Status update emitted by calibration bridge."""
    state: BridgeStateValue
    message: NotRequired[str]


class GestureMatchPayload(TypedDict):
    """Result from comparing current gesture against gesture template."""
    gestureId: str | None
    name: str | None
    score: float
    timestamp: float | None
    matched: bool
    hasTemplates: bool
    threshold: NotRequired[float]
    triggered: NotRequired[bool]
    key: NotRequired[str | None]
    injectionError: NotRequired[str]
    keyAction: NotRequired[KeyActionValue]


class CalibrationUpdatePayload(TypedDict):
    """Progress update of gesture calibration."""
    repCount: int
    capturing: bool
    phase: CapturePhaseValue
    countdownRemaining: float


class PosePayload(TypedDict):
    """Result of pose estimation from processed camera frame."""
    detected: bool
    landmarks: Any
    visibility: Any
    timestampMs: int
    renderJoints: NotRequired[list[str]]
