from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import Any

from backend.matching_engine import AngleKey, TemplateBuilder
from backend.matching_engine.core.angles import reduce_joints

from ..bridges.bridge_types import CalibrationUpdatePayload
from ..gestures.gesture_regions import infer_gesture_regions
from ..gestures.gesture_store import GestureStore, SavedGesture
from ..utils.logging_utils import log_info
from .calibration_capture import CalibrationCaptureController, CapturePhase


class CalibrationService:
    def __init__(
        self,
        gesture_store: GestureStore,
        *,
        on_update: Callable[[CalibrationUpdatePayload], None] | None = None,
        capture_controller: CalibrationCaptureController | None = None,
        template_builder: TemplateBuilder | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._gesture_store = gesture_store
        self._on_update = on_update
        self._capture = capture_controller or CalibrationCaptureController()
        self._template_builder = template_builder or TemplateBuilder()
        self._clock = clock
        self._frames: list[Mapping[AngleKey, float]] = []
        self._reps: list[dict[AngleKey, float] | list[dict[AngleKey, float]]] = []
        self._recording = False

    @property
    def recording(self) -> bool:
        return self._recording

    @property
    def capture_phase(self) -> CapturePhase:
        return self._capture.phase

    def add_pose_angles(self, angles: Mapping[AngleKey, float]) -> None:
        if angles:
            self._frames.append(dict(angles))

        if not self._recording:
            return

        if self._capture.update(angles, self._clock()):
            self._finalize_automatic_rep()
        else:
            self._emit_update()

    def start_calibration(self) -> None:
        self._frames = []
        self._reps = []
        self._recording = False
        self._capture.reset()
        self._emit_update()

    def start_rep(self, recording_seconds: float = 10.0) -> None:
        self._frames = []
        self._capture.start(self._clock(), recording_seconds)
        self._recording = True
        self._emit_update()

    def cancel_rep(self) -> None:
        self._frames = []
        self._recording = False
        self._capture.cancel()
        self._emit_update()

    def stop_rep(self) -> dict[str, Any]:
        if not self._recording:
            raise ValueError("Start recording before stopping this rep.")

        self._recording = False
        frames = list(self._capture.frames or self._frames)
        if not frames:
            self._capture.cancel()
            self._emit_update()
            raise ValueError("Hold a pose first before capturing a rep.")

        self._capture.phase = CapturePhase.CAPTURED
        snapshot = reduce_joints(
            frames,
            lambda values: sum(values) / len(values),
        )
        self._frames = []
        self._reps.append(frames)
        self._emit_update()
        return {
            "repCount": len(self._reps),
            "angles": {
                key.value: value for key, value in snapshot.items() if value is not None
            },
        }

    def capture_rep(self) -> dict[str, Any]:
        if self._recording:
            return self.stop_rep()
        if not self._frames:
            raise ValueError("Hold a pose first before capturing a rep.")

        snapshot = reduce_joints(
            self._frames,
            lambda values: sum(values) / len(values),
        )
        self._reps.append(snapshot)
        self._frames = []
        self._emit_update()
        return {
            "repCount": len(self._reps),
            "angles": {
                key.value: value for key, value in snapshot.items() if value is not None
            },
        }

    def reset_reps(self) -> None:
        self.start_calibration()

    def save_rep(self, name: str, gesture_id: str | None = None) -> dict[str, Any]:
        resolved_name = str(name or "").strip()
        if not resolved_name:
            log_info("[calibration_service.save_rep] aborted: empty gesture name")
            raise ValueError("Gesture name is required.")
        if not self._reps:
            log_info("[calibration_service.save_rep] aborted: no captured reps available")
            raise ValueError("Capture at least one rep before saving.")

        template = self._build_template(resolved_name)
        active_joint_names = [joint.value for joint in template.active_joints]
        saved = SavedGesture(
            gesture_id=str(gesture_id or template.gesture_id),
            name=template.name,
            type=template.type,
            regions=infer_gesture_regions(active_joint_names),
            active_joints=active_joint_names,
            target_angles={
                joint.value: float(value)
                for joint, value in template.target_angles.items()
            },
            tolerance_deg={
                joint.value: float(value)
                for joint, value in template.tolerance_deg.items()
            },
            trajectory=list(template.trajectory),
            fps=int(template.fps),
        )
        self._gesture_store.save(saved)
        self.start_calibration()
        return {
            "gestureId": saved.gesture_id,
            "name": saved.name,
            "repCount": 0,
        }

    def cancel(self) -> None:
        self._recording = False
        self._capture.cancel()

    def _build_template(self, name: str):
        if any(isinstance(rep, list) for rep in self._reps):
            motion_reps = [rep if isinstance(rep, list) else [rep] for rep in self._reps]
            return self._template_builder.build(motion_reps, name=name, mode="motion")

        static_reps = [rep for rep in self._reps if isinstance(rep, dict)]
        active_joints = [
            joint
            for joint in AngleKey
            if any(rep.get(joint) is not None for rep in static_reps)
        ]
        return self._template_builder.build(
            [[rep] for rep in static_reps],
            name=name,
            active_joints=active_joints or None,
        )

    def _finalize_automatic_rep(self) -> None:
        frames = list(self._capture.frames)
        self._recording = False
        if not frames:
            self._capture.cancel()
        else:
            self._reps.append(frames)
            self._frames = []
        self._emit_update()

    def _emit_update(self) -> None:
        if self._on_update is None:
            return
        payload: CalibrationUpdatePayload = {
            "repCount": len(self._reps),
            "capturing": self._recording,
            "phase": self._capture.phase.value,
            "countdownRemaining": self._capture.remaining_seconds(self._clock()),
        }
        self._on_update(payload)
