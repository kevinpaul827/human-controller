"""Matching Engine (v1) - joint-angle state matching + gesture templates.

Public API:
    - Feature extraction: ``FeatureExtractor``, ``AngleKey``, ``PoseLandmarks``
    - Matching: ``PoseMatcher``, ``MatcherStrategy``, ``MatchResult``
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
from .matching import MatcherStrategy, PoseMatcher, state_score
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
    "state_score",
    "AngleSmoother",
    "TemplateBuilder",
]
