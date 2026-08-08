from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

from backend.matching_engine.core.angles import AngleKey, FeatureExtractor
from backend.matching_engine.core.types import MatchResult
from backend.matching_engine.matching.motion_matcher import MotionMatcher
from backend.matching_engine.matching.pose_matcher import PoseMatcher
from backend.pose_types import PoseLandmarks

from .gesture_store import DEFAULT_GESTURES_DIR, GestureStore

DEFAULT_MATCH_THRESHOLD = 0.75
MOTION_WINDOW_FRAMES = 150
MOTION_MIN_TEMPLATE_RANGE_DEG = 15.0


@dataclass
class GestureMatchEvent:
    gestureId: str | None
    name: str | None
    score: float
    timestamp: float | None
    matched: bool
    hasTemplates: bool
    gestureType: str | None = None
    threshold: float = DEFAULT_MATCH_THRESHOLD

    def to_dict(self) -> dict[str, Any]:
        return {
            "gestureId": self.gestureId,
            "name": self.name,
            "score": float(self.score),
            "timestamp": self.timestamp,
            "matched": self.matched,
            "hasTemplates": self.hasTemplates,
            "gestureType": self.gestureType,
            "threshold": float(self.threshold),
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
        self.motion_matcher = MotionMatcher(
            step_pattern="symmetric2",
            open_begin=True,
            min_amplitude_ratio=0.5,
            end_pose_tol_deg=15.0,
            min_template_range_deg=MOTION_MIN_TEMPLATE_RANGE_DEG,
            coverage_tol_deg=20.0,
        )
        self.feature_extractor = FeatureExtractor()
        self.match_threshold = float(match_threshold)
        self._templates = []
        self._state_templates = []
        self._motion_templates = []
        self._templates_by_id: dict[str, str] = {}
        self._template_types: dict[str, str] = {}
        self._active_gesture_ids: set[str] | None = None
        self._match_thresholds: dict[str, float] = {}
        self._active_angle_keys: set[AngleKey] = set()
        self._motion_window = deque(maxlen=MOTION_WINDOW_FRAMES)
        self.reload_templates()

    def reload_templates(self) -> None:
        self.set_saved_gestures(self.store.load_all())

    def set_saved_gestures(self, saved_gestures) -> None:
        self._templates = [gesture.to_template() for gesture in saved_gestures]
        self._templates_by_id = {
            gesture.gesture_id: gesture.name for gesture in saved_gestures
        }
        self._template_types = {
            gesture.gesture_id: gesture.type for gesture in saved_gestures
        }
        self._refresh_active_templates()

    def set_active_gestures(
        self,
        gesture_ids,
        match_thresholds: dict[str, float] | None = None,
    ) -> None:
        self._active_gesture_ids = (
            None
            if gesture_ids is None
            else {str(gesture_id) for gesture_id in gesture_ids if gesture_id}
        )
        self._match_thresholds = {
            str(gesture_id): min(1.0, max(0.0, float(threshold)))
            for gesture_id, threshold in (match_thresholds or {}).items()
            if gesture_id
        }
        self._refresh_active_templates()

    def _refresh_active_templates(self) -> None:
        active_templates = (
            self._templates
            if self._active_gesture_ids is None
            else [
                template
                for template in self._templates
                if template.gesture_id in self._active_gesture_ids
            ]
        )
        self._state_templates = [
            template for template in active_templates if template.type != "motion"
        ]
        self._motion_templates = [
            template for template in active_templates if template.type == "motion"
        ]

        self._active_angle_keys = set()
        for template in active_templates:
            self._active_angle_keys.update(
                key for key in template.active_joints if isinstance(key, AngleKey)
            )
            self._active_angle_keys.update(
                key for key in template.target_angles if isinstance(key, AngleKey)
            )
            for frame in template.trajectory:
                for joint_name in frame:
                    try:
                        self._active_angle_keys.add(AngleKey(joint_name))
                    except ValueError:
                        continue
        self._motion_window.clear()

    def threshold_for(self, gesture_id: str) -> float:
        return self._match_thresholds.get(str(gesture_id), self.match_threshold)

    @property
    def match_thresholds(self) -> dict[str, float]:
        return dict(self._match_thresholds)

    @property
    def bound_angle_keys(self) -> set[AngleKey]:
        return set(self._active_angle_keys)

    @property
    def active_angle_keys(self) -> frozenset[AngleKey]:
        return frozenset(self._active_angle_keys)

    @property
    def active_gesture_ids(self) -> frozenset[str] | None:
        if self._active_gesture_ids is None:
            return None
        return frozenset(self._active_gesture_ids)

    def angles_for_pose(
        self,
        pose: PoseLandmarks | None,
        keys=None,
    ) -> dict:
        if pose is None:
            return {}

        image_plane_pose = PoseLandmarks(
            xyz=pose.xyz.copy(),
            visibility=pose.visibility.copy(),
        )
        image_plane_pose.xyz[:, 2] = 0.0
        return self.feature_extractor.to_angles(image_plane_pose, keys)

    def match_pose(
        self,
        pose: PoseLandmarks | None,
        *,
        angles: dict | None = None,
    ) -> GestureMatchEvent:
        has_templates = bool(self._state_templates or self._motion_templates)
        if pose is None:
            self._motion_window.clear()
            return GestureMatchEvent(
                gestureId=None,
                name=None,
                score=0.0,
                timestamp=None,
                matched=False,
                hasTemplates=has_templates,
            )

        if not has_templates:
            self._motion_window.clear()
            return GestureMatchEvent(
                gestureId=None,
                name=None,
                score=0.0,
                timestamp=None,
                matched=False,
                hasTemplates=False,
            )

        if angles is None:
            keys = (
                self._active_angle_keys
                if self._active_gesture_ids is not None
                else None
            )
            angles = self.angles_for_pose(pose, keys)

        self._motion_window.append(angles)
        timestamp = time.time()
        candidates = [
            MatchResult(
                gesture_id=template.gesture_id,
                score=self.pose_matcher.score(angles, template),
                timestamp=timestamp,
            )
            for template in self._state_templates
        ]
        motion_window = list(self._motion_window)
        candidates.extend(
            MatchResult(
                gesture_id=template.gesture_id,
                score=self.motion_matcher.score(motion_window, template),
                timestamp=timestamp,
            )
            for template in self._motion_templates
        )

        passing = [
            candidate
            for candidate in candidates
            if candidate.score >= self.threshold_for(candidate.gesture_id)
        ]
        result = max(
            passing or candidates,
            key=lambda candidate: candidate.score,
            default=None,
        )
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
        gesture_type = self._template_types.get(result.gesture_id)
        threshold = self.threshold_for(result.gesture_id)
        matched = result.score >= threshold
        if matched and gesture_type == "motion":
            self._motion_window.clear()

        return GestureMatchEvent(
            gestureId=result.gesture_id,
            name=name,
            score=result.score,
            timestamp=result.timestamp,
            matched=matched,
            hasTemplates=True,
            gestureType=gesture_type,
            threshold=threshold,
        )
