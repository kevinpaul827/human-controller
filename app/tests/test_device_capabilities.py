import unittest
from unittest.mock import patch

from app.device_capabilities import (
    GIBIBYTE,
    device_pose_recommendation,
    select_pose_model,
)


class DeviceCapabilitiesTests(unittest.TestCase):
    def test_heavy_requires_high_memory_and_eight_physical_cores(self):
        self.assertEqual(select_pose_model(15, 8), "heavy")
        self.assertEqual(select_pose_model(16, 8), "heavy")
        self.assertEqual(select_pose_model(14.9, 8), "full")
        self.assertEqual(select_pose_model(16, 7), "full")

    def test_full_requires_midrange_memory_and_four_physical_cores(self):
        self.assertEqual(select_pose_model(7, 4), "full")
        self.assertEqual(select_pose_model(8, 4), "full")
        self.assertEqual(select_pose_model(6.9, 4), "lite")
        self.assertEqual(select_pose_model(8, 3), "lite")

    def test_missing_physical_count_uses_logical_thresholds(self):
        self.assertEqual(select_pose_model(16, None, 12), "heavy")
        self.assertEqual(select_pose_model(8, None, 6), "full")
        self.assertEqual(select_pose_model(16, None, 11), "full")
        self.assertEqual(select_pose_model(8, None, 5), "lite")
        self.assertEqual(select_pose_model(16, 4, 16), "full")

    def test_unknown_hardware_uses_lite(self):
        self.assertEqual(select_pose_model(None, 8), "lite")
        self.assertEqual(select_pose_model(16, None, None), "lite")

    @patch("app.device_capabilities.psutil.cpu_count")
    @patch("app.device_capabilities.psutil.virtual_memory")
    def test_device_recommendation_reports_detected_hardware(
        self,
        virtual_memory,
        cpu_count,
    ):
        virtual_memory.return_value.total = 16 * GIBIBYTE
        cpu_count.side_effect = lambda logical: 12 if logical else 8

        recommendation = device_pose_recommendation()

        self.assertEqual(
            recommendation,
            {
                "poseModel": "heavy",
                "ramGb": 16.0,
                "physicalCpuCount": 8,
                "logicalCpuCount": 12,
            },
        )

    @patch("app.device_capabilities.psutil.cpu_count")
    @patch("app.device_capabilities.psutil.virtual_memory")
    def test_missing_physical_count_is_reported_as_unknown(
        self,
        virtual_memory,
        cpu_count,
    ):
        virtual_memory.return_value.total = 8 * GIBIBYTE
        cpu_count.side_effect = lambda logical: 6 if logical else None

        recommendation = device_pose_recommendation()

        self.assertEqual(recommendation["poseModel"], "full")
        self.assertIsNone(recommendation["physicalCpuCount"])
        self.assertEqual(recommendation["logicalCpuCount"], 6)

    @patch("app.device_capabilities.psutil.cpu_count", return_value=8)
    @patch("app.device_capabilities.psutil.virtual_memory")
    def test_invalid_memory_is_reported_as_unknown(
        self,
        virtual_memory,
        _cpu_count,
    ):
        virtual_memory.return_value.total = float("nan")

        recommendation = device_pose_recommendation()

        self.assertEqual(recommendation["poseModel"], "lite")
        self.assertIsNone(recommendation["ramGb"])


if __name__ == "__main__":
    unittest.main()
