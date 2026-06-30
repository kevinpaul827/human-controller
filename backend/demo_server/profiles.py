from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from backend.matching_engine import GestureTemplate

DEFAULT_PATH = Path(__file__).parent / "profiles" / "demo.json"


class ProfileStore:
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

    def summaries(self) -> List[Dict[str, object]]:
        return [
            {
                "gesture_id": t.gesture_id,
                "name": t.name,
                "active_joints": [j.value for j in t.active_joints],
                "target_angles": {k.value: round(v) for k, v in t.target_angles.items()},
            }
            for t in self._templates.values()
        ]
