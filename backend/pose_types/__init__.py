"""Shared contract, produced by perception and consumed by matching_engine."""

from .landmarks import NUM_LANDMARKS, BlazePose33, PoseLandmarks

__all__ = [
    "NUM_LANDMARKS",
    "BlazePose33",
    "PoseLandmarks",
]
