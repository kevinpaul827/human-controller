"""Matching Engine - joint-angle state matching (v1) + DTW motion matching (v2).

Public API:
    - Feature extraction: ``FeatureExtractor``, ``AngleKey``, ``PoseLandmarks``
    - Matching: ``PoseMatcher`` (state), ``MotionMatcher`` (DTW),
      ``MatcherStrategy``, ``MatchResult``
    - Templates: ``TemplateBuilder``, ``GestureTemplate``
"""

from .core import (
    AngleKey,
    AngleVector,
    BlazePose33,
    FeatureExtractor,
    GestureTemplate,
    MatchResult,
    PoseLandmarks,
    joint_angle,
)
from .matching import MatcherStrategy, MotionMatcher, PoseMatcher, dtw_distance, state_score
from .smoothing import AngleSmoother
from .templates import TemplateBuilder

__all__ = [
    "AngleKey",
    "AngleVector",
    "BlazePose33",
    "FeatureExtractor",
    "GestureTemplate",
    "MatchResult",
    "PoseLandmarks",
    "joint_angle",
    "MatcherStrategy",
    "PoseMatcher",
    "MotionMatcher",
    "dtw_distance",
    "state_score",
    "AngleSmoother",
    "TemplateBuilder",
]
