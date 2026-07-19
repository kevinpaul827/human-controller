"""Throwaway gesture store for the debug harness.

Intentionally NOT the production ``ProfileManager``: this is a minimal JSON dump
under a gitignored ``data/`` dir, used only so hand-recorded gestures survive a
harness restart while poking at the engine. Do not depend on it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from backend.matching_engine import GestureTemplate

DEFAULT_PATH = Path(__file__).parent / "data" / "debug_gestures.json"


class DebugGestureStore:
    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, GestureTemplate] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        for d in data.get("gestures", []):
            t = GestureTemplate.from_dict(d)
            self._templates[t.gesture_id] = t

    def _save(self) -> None:
        data = {"gestures": [t.to_dict() for t in self._templates.values()]}
        self.path.write_text(json.dumps(data, indent=2))

    def add(self, template: GestureTemplate) -> GestureTemplate:
        self._templates[template.gesture_id] = template
        self._save()
        return template

    def delete(self, gesture_id: str) -> bool:
        if gesture_id in self._templates:
            del self._templates[gesture_id]
            self._save()
            return True
        return False

    def clear(self) -> None:
        self._templates.clear()
        self._save()

    def all(self) -> List[GestureTemplate]:
        return list(self._templates.values())

    def by_kind(self, kind: str) -> List[GestureTemplate]:
        """Templates matching a match kind: 'state' or 'motion'."""
        return [t for t in self._templates.values() if t.type == kind]

    def name_for(self, gesture_id: str) -> str:
        t = self._templates.get(gesture_id)
        return t.name if t else gesture_id

    def summaries(self) -> List[Dict[str, object]]:
        return [
            {
                "gesture_id": t.gesture_id,
                "name": t.name,
                "kind": t.type,
                "active_joints": [j.value for j in t.active_joints],
                "target_angles": {k.value: round(v) for k, v in t.target_angles.items()},
                "trajectory_len": len(t.trajectory),
            }
            for t in self._templates.values()
        ]
