from __future__ import annotations

from pathlib import Path

# Bundled model options, ordered from least to most demanding.
DEFAULT_POSE_MODEL = "lite"
POSE_MODEL_VARIANTS = ("lite", "full", "heavy")

POSE_MODEL_PATHS = {
    variant: Path(__file__).resolve().parent / f"pose_landmarker_{variant}.task"
    for variant in POSE_MODEL_VARIANTS
}


def normalize_pose_model(value: object) -> str:
    if not isinstance(value, str):
        return DEFAULT_POSE_MODEL
    normalized = value.strip().lower()
    if normalized not in POSE_MODEL_PATHS:
        return DEFAULT_POSE_MODEL
    return normalized


def pose_model_path(value: object) -> Path:
    return POSE_MODEL_PATHS[normalize_pose_model(value)]
