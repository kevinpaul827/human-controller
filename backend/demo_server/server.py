from __future__ import annotations

from collections import deque
from typing import Deque, List, Optional

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.matching_engine import (
    AngleKey,
    AngleSmoother,
    AngleVector,
    FeatureExtractor,
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

WINDOW = 12

from .profiles import ProfileStore

MATCH_THRESHOLD = 0.55
builder = TemplateBuilder(min_tolerance_deg=20.0, tolerance_k=2.0)
fx = FeatureExtractor()
matcher = PoseMatcher()
store = ProfileStore()

app = FastAPI(title="Gesture demo")
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
    xyz[:, 2] = 0.0  # drop z
    visibility = np.asarray(vis, dtype=np.float64) if vis else np.ones(NUM_LANDMARKS)
    return PoseLandmarks(xyz=xyz, visibility=visibility)


def _angle_payload(angles: AngleVector, active: set[AngleKey] | None = None) -> dict:
    keys = active if active is not None else set(AngleKey)
    return {
        joint.value: (None if angles.get(joint) is None else round(angles[joint]))
        for joint in AngleKey
        if joint in keys
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True, "gestures": len(store.all())}


@app.websocket("/ws")
async def ws(socket: WebSocket) -> None:
    await socket.accept()
    mode = "idle"
    reps: List[AngleVector] = []
    window: Deque[AngleVector] = deque(maxlen=WINDOW)
    smoother = AngleSmoother(alpha=0.25, deadband_deg=2.0)
    focus_regions: list[BodyRegion] = list(BodyRegion)
    focus_angles = default_focus_angle_keys()
    await socket.send_json({"type": "gestures", "items": store.summaries()})

    try:
        while True:
            msg = await socket.receive_json()
            mtype = msg.get("type")

            if mtype == "set_mode":
                mode = msg.get("mode", "idle")
                smoother.reset()
                window.clear()
                if mode != "calibrate":
                    reps = []

            elif mtype == "set_focus_regions":
                focus_regions = parse_regions(msg.get("regions"))
                focus_angles = angle_keys_for_regions(focus_regions)
                smoother.reset()
                window.clear()
                if mode == "calibrate":
                    reps = []
                await socket.send_json({
                    "type": "focus_regions",
                    "regions": [r.value for r in focus_regions],
                    "reps_cleared": mode == "calibrate",
                })

            elif mtype == "start_calibration":
                if msg.get("regions") is not None:
                    focus_regions = parse_regions(msg.get("regions"))
                    focus_angles = angle_keys_for_regions(focus_regions)
                mode = "calibrate"
                reps = []
                window.clear()
                smoother.reset()
                await socket.send_json({
                    "type": "calibration",
                    "reps": 0,
                    "regions": [r.value for r in focus_regions],
                })

            elif mtype == "frame":
                lm = _to_landmarks(msg)
                if lm is None:
                    continue
                angles = mask_angles(smoother.update(fx.to_angles(lm)), focus_angles)
                window.append(angles)
                reply: dict = {
                    "type": "tick",
                    "angles": _angle_payload(angles, focus_angles),
                    "regions": [r.value for r in focus_regions],
                }
                if mode == "match":
                    result = matcher.best_match(angles, store.all())
                    if result is not None:
                        reply["match"] = {
                            "gesture_id": result.gesture_id,
                            "name": _name_for(result.gesture_id),
                            "score": round(result.score, 3),
                            "matched": result.score >= MATCH_THRESHOLD,
                        }
                await socket.send_json(reply)

            elif mtype == "capture_rep":
                if not window:
                    await socket.send_json({"type": "error", "message": "Hold a pose first"})
                else:
                    snapshot = reduce_joints(list(window), np.mean)
                    reps.append(snapshot)
                    window.clear()
                    await socket.send_json({
                        "type": "rep_captured",
                        "rep": len(reps),
                        "angles": _angle_payload(snapshot, focus_angles),
                    })

            elif mtype == "save_gesture":
                name = (msg.get("name") or "").strip()
                if not name:
                    await socket.send_json({"type": "error", "message": "Name required"})
                elif not reps:
                    await socket.send_json({"type": "error", "message": "Capture at least one rep"})
                else:
                    template = builder.build(
                        [[r] for r in reps],
                        name=name,
                        active_joints=sorted(focus_angles, key=lambda k: k.value),
                    )
                    store.add(template)
                    print(
                        f"[demo] saved '{name}' from {len(reps)} reps -> "
                        f"{len(template.target_angles)} angles: "
                        + ", ".join(f"{k.value}={v:.0f}" for k, v in template.target_angles.items())
                    )
                    reps = []
                    window.clear()
                    mode = "idle"
                    await socket.send_json({
                        "type": "saved",
                        "gesture": {"gesture_id": template.gesture_id, "name": template.name},
                    })
                    await socket.send_json({"type": "gestures", "items": store.summaries()})

            elif mtype == "cancel_calibration":
                reps = []
                window.clear()
                mode = "idle"

            elif mtype == "delete_gesture":
                store.delete(msg.get("id", ""))
                await socket.send_json({"type": "gestures", "items": store.summaries()})

            elif mtype == "clear_gestures":
                store.clear()
                await socket.send_json({"type": "gestures", "items": store.summaries()})

            elif mtype == "list_gestures":
                await socket.send_json({"type": "gestures", "items": store.summaries()})

    except WebSocketDisconnect:
        return


def _name_for(gesture_id: str) -> str:
    for t in store.all():
        if t.gesture_id == gesture_id:
            return t.name
    return gesture_id
