from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.matching_engine.core.angles import FeatureExtractor
from backend.matching_engine.matching.pose_matcher import PoseMatcher
from backend.pose_types import PoseLandmarks

from .gesture_store import DEFAULT_GESTURES_DIR, GestureStore

DEFAULT_MATCH_THRESHOLD = 0.75


@dataclass
class GestureMatchEvent:
    gestureId: str | None
    name: str | None
    score: float
    timestamp: float | None
    matched: bool
    hasTemplates: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "gestureId": self.gestureId,
            "name": self.name,
            "score": float(self.score),
            "timestamp": self.timestamp,
            "matched": self.matched,
            "hasTemplates": self.hasTemplates,
        }


class GestureMatcher:
    def __init__(
        self,
        gestures_dir: Path = DEFAULT_GESTURES_DIR,
        *,
        match_threshold: float = DEFAULT_MATCH_THRESHOLD,
    ) -> None:
        self.store = GestureStore(gestures_dir)
        self.pose_matcher = PoseMatcher()
        self.feature_extractor = FeatureExtractor()
        self.match_threshold = float(match_threshold)
        self._templates = []
        self._templates_by_id: dict[str, str] = {}
        self.reload_templates()

    def reload_templates(self) -> None:
        saved_gestures = self.store.load_all()
        self.set_saved_gestures(saved_gestures)

    def set_saved_gestures(self, saved_gestures) -> None:
        self._templates = [gesture.to_template() for gesture in saved_gestures]
        self._templates_by_id = {
            gesture.gesture_id: gesture.name for gesture in saved_gestures
        }

    def angles_for_pose(self, pose: PoseLandmarks | None) -> dict:
        if pose is None:
            return {}

        return self.feature_extractor.to_angles(pose)

    def match_pose(self, pose: PoseLandmarks | None) -> GestureMatchEvent:
        if pose is None:
            return GestureMatchEvent(
                gestureId=None,
                name=None,
                score=0.0,
                timestamp=None,
                matched=False,
                hasTemplates=bool(self._templates),
            )

        if not self._templates:
            return GestureMatchEvent(
                gestureId=None,
                name=None,
                score=0.0,
                timestamp=None,
                matched=False,
                hasTemplates=False,
            )

        angles = self.angles_for_pose(pose)
        result = self.pose_matcher.best_match(angles, self._templates)
        if result is None:
            return GestureMatchEvent(
                gestureId=None,
                name=None,
                score=0.0,
                timestamp=None,
                matched=False,
                hasTemplates=True,
            )

        name = self._templates_by_id.get(result.gesture_id, result.gesture_id)
        return GestureMatchEvent(
            gestureId=result.gesture_id,
            name=name,
            score=result.score,
            timestamp=result.timestamp,
            matched=result.score >= self.match_threshold,
            hasTemplates=True,
        )
