from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4

from backend.matching_engine.core.types import GestureTemplate

from app.product import APPLICATION_NAME as APP_SUPPORT_DIR_NAME
from .constants import (
    GESTURES_DIR_ENV,
    PROJECT_ROOT_ENV,
)
from ..utils.json_storage import json_path, write_json_atomic


def _production_app_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_SUPPORT_DIR_NAME

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "").strip()
        if appdata:
            return Path(appdata) / APP_SUPPORT_DIR_NAME
        return Path.home() / "AppData" / "Roaming" / APP_SUPPORT_DIR_NAME

    xdg_data_home = os.environ.get("XDG_DATA_HOME", "").strip()
    if xdg_data_home:
        return Path(xdg_data_home) / "human-controller"

    return Path.home() / ".local" / "share" / "human-controller"


def resolve_default_gestures_dir() -> Path:
    explicit_dir = os.environ.get(GESTURES_DIR_ENV, "").strip()
    if explicit_dir:
        return Path(explicit_dir).expanduser().resolve()

    project_root = os.environ.get(PROJECT_ROOT_ENV, "").strip()
    if project_root:
        return Path(project_root).expanduser().resolve() / "app" / "data" / "gestures"

    if getattr(sys, "frozen", False):
        return _production_app_data_dir() / "gestures"

    return Path(__file__).resolve().parent.parent / "data" / "gestures"


DEFAULT_GESTURES_DIR = resolve_default_gestures_dir()


@dataclass
class SavedGesture:
    gesture_id: str = ""
    name: str = ""
    active_joints: list[str] = field(default_factory=list)
    trajectory: list[dict[str, object]] = field(default_factory=list)
    fps: int = 30

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "SavedGesture":
        gesture_id = str(payload.get("gesture_id") or "").strip()
        name = str(payload.get("name") or "").strip()
        if not gesture_id or not name:
            raise ValueError("gesture_id and name are required")

        active_joints = payload.get("active_joints", [])
        trajectory = payload.get("trajectory", [])
        if not isinstance(active_joints, list):
            raise ValueError("active_joints must be a list.")
        if not isinstance(trajectory, list) or not trajectory:
            raise ValueError("Motion gestures require a trajectory.")

        template = GestureTemplate(
            gesture_id=gesture_id,
            name=name,
            active_joints=active_joints,
            trajectory=trajectory,
            fps=int(payload.get("fps", 30)),
        )
        return cls(
            gesture_id=template.gesture_id,
            name=template.name,
            active_joints=[joint.value for joint in template.active_joints],
            trajectory=[
                {
                    joint.value: None if value is None else float(value)
                    for joint, value in frame.items()
                }
                for frame in template.trajectory
            ],
            fps=template.fps,
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def to_summary(self) -> dict[str, str]:
        return {
            "gestureId": self.gesture_id,
            "name": self.name,
        }

    @classmethod
    def from_template(
        cls,
        template: GestureTemplate,
        *,
        gesture_id: str | None = None,
    ) -> "SavedGesture":
        return cls(
            gesture_id=str(gesture_id or template.gesture_id),
            name=template.name,
            active_joints=[joint.value for joint in template.active_joints],
            trajectory=[
                {
                    joint.value: None if value is None else float(value)
                    for joint, value in frame.items()
                }
                for frame in template.trajectory
            ],
            fps=template.fps,
        )

    def to_template(self) -> GestureTemplate:
        return GestureTemplate(
            name=self.name,
            gesture_id=self.gesture_id,
            active_joints=self.active_joints,
            trajectory=self.trajectory,
            fps=self.fps,
        )


class GestureStore:
    def __init__(self, gestures_dir: Path = DEFAULT_GESTURES_DIR) -> None:
        self.gestures_dir = Path(gestures_dir)
        self.gestures_dir.mkdir(parents=True, exist_ok=True)

    def _gesture_path(self, gesture_id: str) -> Path:
        try:
            return json_path(self.gestures_dir, gesture_id, label="Gesture ID")
        except ValueError as error:
            if not str(gesture_id or "").strip():
                raise ValueError("Gesture ID is required.") from error
            raise ValueError("Gesture ID must not contain a path.") from error

    def gesture_path(self, gesture_id: str) -> Path:
        return self._gesture_path(gesture_id)

    def delete(self, gesture_id: str) -> None:
        path = self._gesture_path(gesture_id)
        if path.exists():
            path.unlink()

    def _make_gesture_id(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
        if not slug:
            slug = f"gesture_{uuid4().hex[:8]}"
        return slug[:64]

    def save(self, gesture: SavedGesture) -> Path:
        validated = SavedGesture.from_dict(gesture.to_dict())
        path = self._gesture_path(validated.gesture_id)
        write_json_atomic(path, validated.to_dict())
        return path

    def create_motion(
        self,
        *,
        name: str,
        active_joints: list[str],
        trajectory: list[dict[str, object]],
        gesture_id: str | None = None,
        fps: int = 30,
    ) -> SavedGesture:
        resolved_gesture_id = gesture_id or self._make_gesture_id(name)
        gesture = SavedGesture(
            gesture_id=resolved_gesture_id,
            name=name,
            active_joints=active_joints,
            trajectory=trajectory,
            fps=fps,
        )
        self.save(gesture)
        return self.load(resolved_gesture_id)

    def load(self, gesture_id: str) -> SavedGesture:
        payload = json.loads(self._gesture_path(gesture_id).read_text(encoding="utf-8"))
        return SavedGesture.from_dict(payload)

    def load_all(self) -> list[SavedGesture]:
        gestures: list[SavedGesture] = []
        for path in sorted(self.gestures_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                gestures.append(SavedGesture.from_dict(payload))
            except (json.JSONDecodeError, OSError, ValueError):
                continue
        return sorted(gestures, key=lambda gesture: gesture.name.lower())

    def list_gestures(self) -> list[dict[str, str]]:
        return [gesture.to_summary() for gesture in self.load_all()]
