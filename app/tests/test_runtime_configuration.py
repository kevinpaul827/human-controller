import math
import unittest

from app.core.runtime_configuration import RuntimeConfiguration, bounded_number


class RuntimeConfigurationTests(unittest.TestCase):
    def test_valid_payload_is_normalized_for_runtime_consumers(self) -> None:
        runtime = RuntimeConfiguration.from_payload(
            {
                "settings": {
                    "matchThreshold": 72,
                    "holdDuration": 1.2,
                    "cooldown": 0.4,
                    "smoothing": 3,
                    "poseModel": "HEAVY",
                },
                "bindings": {"elbow": "E"},
                "matchThresholds": {"elbow": 64},
            }
        )

        self.assertEqual(runtime.bindings, {"elbow": "E"})
        self.assertEqual(runtime.match_thresholds, {"elbow": 64.0})
        self.assertEqual(runtime.settings["poseModel"], "heavy")
        self.assertEqual(runtime.settings["smoothing"], 3)

    def test_invalid_payload_uses_safe_defaults_and_discards_empty_bindings(self) -> None:
        runtime = RuntimeConfiguration.from_payload(
            {
                "settings": {
                    "matchThreshold": "not-a-number",
                    "holdDuration": math.inf,
                    "cooldown": -2,
                    "smoothing": 99,
                    "poseModel": "unknown",
                },
                "bindings": {"": "A", "valid": ""},
                "matchThresholds": {"gesture": math.nan},
            }
        )

        self.assertEqual(runtime.bindings, {})
        self.assertEqual(runtime.settings["matchThreshold"], 75.0)
        self.assertEqual(runtime.settings["holdDuration"], 1.5)
        self.assertEqual(runtime.settings["cooldown"], 0.0)
        self.assertEqual(runtime.settings["smoothing"], 4)
        self.assertEqual(runtime.settings["poseModel"], "lite")
        self.assertEqual(runtime.match_thresholds["gesture"], 75.0)

    def test_bounded_number_rejects_non_finite_values(self) -> None:
        for value in (math.nan, math.inf, -math.inf, None, "invalid"):
            with self.subTest(value=value):
                self.assertEqual(bounded_number(value, 5.0, 0.0, 10.0), 5.0)


if __name__ == "__main__":
    unittest.main()
