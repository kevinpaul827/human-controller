"""DEBUG HARNESS WebSocket server — NOT FOR PRODUCTION.

Wires the matching engine together for manual testing: it receives BlazePose
landmarks from the browser page, smooths them into joint angles, and runs either
v1 state matching (:class:`PoseMatcher`) or v2 DTW motion matching
(:class:`MotionMatcher`) depending on the selected "kind".

Persistence is a throwaway JSON store (:class:`DebugGestureStore`), deliberately
NOT the production ``ProfileManager``.
"""

from __future__ import annotations

from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Deque, List, Optional, Union

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.matching_engine import (
    AngleKey,
    AngleSmoother,
    AngleVector,
    FeatureExtractor,
    GestureTemplate,
    MotionMatcher,
    PoseLandmarks,
    PoseMatcher,
    TemplateBuilder,
)
from backend.matching_engine.core.angles import (
    angle_keys_for_regions,
    default_focus_angle_keys,
    mask_angles,
    reduce_joints,
)
from backend.pose_types import NUM_LANDMARKS, BodyRegion, parse_regions

from .store import DebugGestureStore

# Rolling buffer of recent frames. Large enough to hold a slow (~5s) movement;
# subsequence DTW then finds the gesture anywhere in that tail.
MOTION_WINDOW = 150
STATE_SNAPSHOT = 12
MOTION_MIN_FRAMES = 8
MATCH_THRESHOLD = 0.55

STATIC_DIR = Path(__file__).parent / "static"

fx = FeatureExtractor()
builder = TemplateBuilder(min_tolerance_deg=20.0, tolerance_k=2.0)
state_matcher = PoseMatcher()
# Live matching: subsequence DTW (open-begin) with a speed-unbounded weighted
# step pattern (any speed matches), gated on motion amplitude so small wiggles
# can't match a large gesture.
motion_matcher = MotionMatcher(
    step_pattern="symmetric2",
    open_begin=True,
    min_amplitude_ratio=0.5,
    end_pose_tol_deg=15.0,
)
store = DebugGestureStore()

@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    print("=" * 68)
    print("  DEBUG HARNESS running — manual matching-engine testing only.")
    print("  Not part of the production app; uses a throwaway gesture store.")
    print("  Open http://localhost:8000/ in a browser.")
    print("=" * 68)
    yield


app = FastAPI(
    title="Matching-engine DEBUG HARNESS (not for production)",
    lifespan=_lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_landmarks(msg: dict) -> Optional[PoseLandmarks]:
    lm = msg.get("landmarks")
    vis = msg.get("visibility")
    if not lm or len(lm) != NUM_LANDMARKS:
        return None
    xyz = np.asarray(lm, dtype=np.float64)
    if xyz.shape != (NUM_LANDMARKS, 3):
        return None
    xyz[:, 2] = 0.0  # drop z; angles are computed in the image plane
    visibility = np.asarray(vis, dtype=np.float64) if vis else np.ones(NUM_LANDMARKS)
    return PoseLandmarks(xyz=xyz, visibility=visibility)


def _angle_payload(angles: AngleVector, keys: set[AngleKey]) -> dict:
    return {
        joint.value: (None if angles.get(joint) is None else round(angles[joint]))
        for joint in AngleKey
        if joint in keys
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True, "gestures": len(store.all())}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})


class Session:
    """Per-connection state for the debug harness."""

    def __init__(self) -> None:
        self.mode = "idle"                     # idle | calibrate | match
        self.kind = "state"                    # state | motion
        self.window: Deque[AngleVector] = deque(maxlen=MOTION_WINDOW)
        self.smoother = AngleSmoother(alpha=0.25, deadband_deg=2.0)
        self.focus_regions: List[BodyRegion] = list(BodyRegion)
        self.focus_angles = default_focus_angle_keys()
        # State calibration: list of averaged snapshots.
        # Motion calibration: list of frame sequences.
        self.reps: List[Union[AngleVector, List[AngleVector]]] = []
        self.recording = False
        self.current_rep: List[AngleVector] = []

    def reset_live(self) -> None:
        self.smoother.reset()
        self.window.clear()
        self.recording = False
        self.current_rep = []


async def _send_gestures(socket: WebSocket) -> None:
    await socket.send_json({"type": "gestures", "items": store.summaries()})


@app.websocket("/ws")
async def ws(socket: WebSocket) -> None:
    await socket.accept()
    s = Session()
    await socket.send_json({
        "type": "hello",
        "kind": s.kind,
        "regions": [r.value for r in s.focus_regions],
    })
    await _send_gestures(socket)

    try:
        while True:
            msg = await socket.receive_json()
            mtype = msg.get("type")

            if mtype == "set_kind":
                s.kind = "motion" if msg.get("kind") == "motion" else "state"
                s.mode = "idle"
                s.reps = []
                s.reset_live()
                await socket.send_json({"type": "kind", "kind": s.kind})

            elif mtype == "set_mode":
                s.mode = msg.get("mode", "idle")
                s.reset_live()
                if s.mode != "calibrate":
                    s.reps = []

            elif mtype == "set_focus_regions":
                s.focus_regions = parse_regions(msg.get("regions"))
                s.focus_angles = angle_keys_for_regions(s.focus_regions)
                s.reset_live()
                if s.mode == "calibrate":
                    s.reps = []
                await socket.send_json({
                    "type": "focus_regions",
                    "regions": [r.value for r in s.focus_regions],
                    "reps_cleared": s.mode == "calibrate",
                })

            elif mtype == "start_calibration":
                if msg.get("regions") is not None:
                    s.focus_regions = parse_regions(msg.get("regions"))
                    s.focus_angles = angle_keys_for_regions(s.focus_regions)
                if msg.get("kind") in ("state", "motion"):
                    s.kind = msg["kind"]
                s.mode = "calibrate"
                s.reps = []
                s.reset_live()
                await socket.send_json({
                    "type": "calibration",
                    "kind": s.kind,
                    "reps": 0,
                    "regions": [r.value for r in s.focus_regions],
                })

            elif mtype == "frame":
                lm = _to_landmarks(msg)
                if lm is None:
                    continue
                angles = mask_angles(s.smoother.update(fx.to_angles(lm)), s.focus_angles)
                s.window.append(angles)
                if s.recording:
                    s.current_rep.append(angles)
                reply: dict = {
                    "type": "tick",
                    "angles": _angle_payload(angles, s.focus_angles),
                    "regions": [r.value for r in s.focus_regions],
                    "recording": s.recording,
                    "rec_frames": len(s.current_rep),
                }
                if s.mode == "match":
                    result = _match(s)
                    if result is not None:
                        reply["match"] = result
                await socket.send_json(reply)

            elif mtype == "capture_rep":  # state calibration
                if not s.window:
                    await socket.send_json({"type": "error", "message": "Hold a pose first"})
                else:
                    snapshot = reduce_joints(list(s.window)[-STATE_SNAPSHOT:], np.mean)
                    s.reps.append(snapshot)
                    s.window.clear()
                    await socket.send_json({
                        "type": "rep_captured",
                        "kind": "state",
                        "rep": len(s.reps),
                        "angles": _angle_payload(snapshot, s.focus_angles),
                    })

            elif mtype == "record_start":  # motion calibration
                s.recording = True
                s.current_rep = []

            elif mtype == "record_stop":
                s.recording = False
                if len(s.current_rep) < MOTION_MIN_FRAMES:
                    await socket.send_json({
                        "type": "error",
                        "message": f"Movement too short ({len(s.current_rep)} frames)",
                    })
                else:
                    s.reps.append(list(s.current_rep))
                    await socket.send_json({
                        "type": "rep_captured",
                        "kind": "motion",
                        "rep": len(s.reps),
                        "frames": len(s.current_rep),
                    })
                s.current_rep = []

            elif mtype == "save_gesture":
                await _save_gesture(socket, s, (msg.get("name") or "").strip())

            elif mtype == "cancel_calibration":
                s.reps = []
                s.reset_live()
                s.mode = "idle"

            elif mtype == "delete_gesture":
                store.delete(msg.get("id", ""))
                await _send_gestures(socket)

            elif mtype == "clear_gestures":
                store.clear()
                await _send_gestures(socket)

            elif mtype == "list_gestures":
                await _send_gestures(socket)

    except WebSocketDisconnect:
        return


def _match(s: Session) -> Optional[dict]:
    results = []
    if s.window and store.by_kind("state"):
        r = state_matcher.best_match(s.window[-1], store.by_kind("state"))
        if r is not None:
            results.append(r)
    if len(s.window) >= MOTION_MIN_FRAMES and store.by_kind("motion"):
        r = motion_matcher.best_match(list(s.window), store.by_kind("motion"))
        if r is not None:
            results.append(r)
    if not results:
        return None
    result = max(results, key=lambda r: r.score)
    return {
        "gesture_id": result.gesture_id,
        "name": store.name_for(result.gesture_id),
        "score": round(result.score, 3),
        "matched": result.score >= MATCH_THRESHOLD,
    }


async def _save_gesture(socket: WebSocket, s: Session, name: str) -> None:
    if not name:
        await socket.send_json({"type": "error", "message": "Name required"})
        return
    if not s.reps:
        await socket.send_json({"type": "error", "message": "Capture at least one rep"})
        return

    active = sorted(s.focus_angles, key=lambda k: k.value)
    if s.kind == "state":
        reps = [[r] for r in s.reps]  # each snapshot is a 1-frame rep
    else:
        reps = list(s.reps)  # each rep is already a frame sequence

    template: GestureTemplate = builder.build(
        reps, name=name, mode=s.kind, active_joints=active
    )
    store.add(template)
    print(f"[debug-harness] saved {s.kind} gesture '{name}' from {len(s.reps)} rep(s)")

    s.reps = []
    s.reset_live()
    s.mode = "idle"
    await socket.send_json({
        "type": "saved",
        "gesture": {"gesture_id": template.gesture_id, "name": template.name, "kind": template.type},
    })
    await _send_gestures(socket)


# Serve the rest of the static assets (if any) under /static.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
