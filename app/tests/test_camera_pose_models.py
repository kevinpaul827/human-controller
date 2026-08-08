import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtGui import QImage

from app.core import pose_processor as pose_processor_module
from app.core.pose_processor import PoseProcessor
from backend.perception.models import (
    DEFAULT_POSE_MODEL,
    POSE_MODEL_PATHS,
    POSE_MODEL_VARIANTS,
    normalize_pose_model,
)
from backend.perception.pose_estimator import PoseEstimator
from scripts import build_macos_app


class PoseModelTests(unittest.TestCase):
    def test_model_names_resolve_to_bundled_assets(self):
        self.assertEqual(POSE_MODEL_VARIANTS, ("lite", "full", "heavy"))
        for model, path in POSE_MODEL_PATHS.items():
            self.assertEqual(path.name, f"pose_landmarker_{model}.task")
            self.assertTrue(path.is_file())

    def test_invalid_model_values_use_lite(self):
        self.assertEqual(normalize_pose_model(None), DEFAULT_POSE_MODEL)
        self.assertEqual(normalize_pose_model("unknown"), DEFAULT_POSE_MODEL)
        self.assertEqual(normalize_pose_model(" FULL "), "full")

    @patch("backend.perception.pose_estimator.PoseLandmarker.create_from_options")
    def test_estimator_uses_selected_model_asset(self, create_detector):
        detector = MagicMock()
        create_detector.return_value = detector

        estimator = PoseEstimator("full")
        options = create_detector.call_args.args[0]

        self.assertEqual(estimator.model, "full")
        self.assertEqual(
            Path(options.base_options.model_asset_path),
            POSE_MODEL_PATHS["full"],
        )
        estimator.close()
        estimator.close()
        detector.close.assert_called_once_with()


class PoseProcessorModelTests(unittest.TestCase):
    def test_switch_closes_estimator_and_repeated_model_is_a_no_op(self):
        processor = PoseProcessor()
        estimator = MagicMock()
        processor.estimator = estimator

        processor.configure_model("full")

        self.assertEqual(processor.model, "full")
        self.assertIsNone(processor.estimator)
        estimator.close.assert_called_once_with()

        next_estimator = MagicMock()
        processor.estimator = next_estimator
        processor.configure_model("full")

        self.assertIs(processor.estimator, next_estimator)
        next_estimator.close.assert_not_called()

    @patch.object(pose_processor_module, "PoseEstimator")
    def test_next_frame_uses_selected_model(self, estimator_type):
        estimator = MagicMock()
        estimator.estimate_pose.return_value = None
        estimator_type.return_value = estimator
        processor = PoseProcessor()
        processor.configure_model("heavy")
        image = QImage(2, 2, QImage.Format.Format_BGR888)
        image.fill(0)

        processor.process_frame(image, 10)

        estimator_type.assert_called_once_with("heavy")
        estimator.estimate_pose.assert_called_once()

    def test_invalid_switch_uses_lite(self):
        processor = PoseProcessor()
        processor.model = "heavy"
        estimator = MagicMock()
        processor.estimator = estimator

        processor.configure_model("invalid")

        self.assertEqual(processor.model, "lite")
        self.assertIsNone(processor.estimator)
        estimator.close.assert_called_once_with()

    def test_close_releases_estimator_once(self):
        processor = PoseProcessor()
        estimator = MagicMock()
        processor.estimator = estimator

        processor.close()
        processor.close()

        self.assertIsNone(processor.estimator)
        estimator.close.assert_called_once_with()


class PoseModelPackagingTests(unittest.TestCase):
    def test_packaged_app_starts_as_a_regular_application(self):
        self.assertNotIn("LSUIElement", build_macos_app.SPEC_TEMPLATE)

    def test_packager_requires_and_bundles_every_model(self):
        expected_names = {
            "pose_landmarker_lite.task",
            "pose_landmarker_full.task",
            "pose_landmarker_heavy.task",
        }

        self.assertEqual(set(build_macos_app.POSE_MODEL_NAMES), expected_names)
        self.assertEqual(
            {path.name for path in build_macos_app.POSE_MODEL_PATHS},
            expected_names,
        )
        self.assertEqual(
            {path.name for path in build_macos_app.BUNDLED_POSE_MODEL_PATHS},
            expected_names,
        )
        for name in expected_names:
            self.assertIn(f'("backend/perception/{name}",', build_macos_app.SPEC_TEMPLATE)


if __name__ == "__main__":
    unittest.main()
