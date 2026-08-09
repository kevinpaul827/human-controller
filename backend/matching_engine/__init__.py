"""Matching Engine - joint-angle DTW motion matching.

Public API:
    - Feature extraction: ``FeatureExtractor``, ``AngleKey``, ``PoseLandmarks``
    - Matching: ``MotionMatcher`` (DTW), ``MatcherStrategy``, ``MatchResult``
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
from .matching import MatcherStrategy, MotionMatcher, dtw_distance
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
    "MotionMatcher",
    "dtw_distance",
    "AngleSmoother",
    "TemplateBuilder",
]
