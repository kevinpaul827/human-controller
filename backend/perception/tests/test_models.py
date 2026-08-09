from backend import perception
from backend.perception.models import (
    DEFAULT_POSE_MODEL,
    POSE_MODEL_VARIANTS,
    normalize_pose_model,
    pose_model_path,
)


def test_perception_package_keeps_estimator_import_explicit():
    assert not hasattr(perception, "PoseEstimator")


def test_pose_model_normalization_and_assets():
    assert normalize_pose_model(" HEAVY ") == "heavy"
    assert normalize_pose_model("unknown") == DEFAULT_POSE_MODEL
    assert normalize_pose_model(None) == DEFAULT_POSE_MODEL
    assert all(pose_model_path(model).is_file() for model in POSE_MODEL_VARIANTS)
