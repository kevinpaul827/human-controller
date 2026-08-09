import math
import unittest

from app.core.trigger_controller import TriggerController


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class TriggerControllerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.controller = TriggerController(self.clock)
        self.controller.configure(
            {"wave": "Space"},
            {"matchThreshold": 75, "cooldown": 0.5, "smoothing": 0},
        )

    def match(self, score=0.9):
        return {
            "gestureId": "wave",
            "score": score,
            "matched": score >= 0.75,
        }

    def test_match_emits_short_key_tap(self):
        self.assertEqual(self.controller.process(self.match())["action"], "press")
        self.clock.advance(0.04)
        self.assertIsNone(self.controller.process(self.match()))
        self.clock.advance(0.01)

        release = self.controller.process(self.match())

        self.assertEqual(release["action"], "release")
        self.assertEqual(release["key"], "Space")

    def test_tap_rearms_only_after_match_clears(self):
        self.controller.process(self.match())
        self.clock.advance(0.05)
        self.controller.process(self.match())
        self.assertIsNone(self.controller.process(self.match()))

        self.controller.process({"gestureId": None, "score": 0, "matched": False})
        self.clock.advance(0.5)

        self.assertEqual(self.controller.process(self.match())["action"], "press")

    def test_cooldown_blocks_early_retrigger(self):
        self.controller.process(self.match())
        self.clock.advance(0.05)
        self.controller.process(self.match())
        self.controller.process({"gestureId": None, "score": 0, "matched": False})
        self.clock.advance(0.44)

        self.assertIsNone(self.controller.process(self.match()))
        self.clock.advance(0.01)
        self.assertEqual(self.controller.process(self.match())["action"], "press")

    def test_unbound_and_low_score_matches_do_not_trigger(self):
        self.assertIsNone(self.controller.process(self.match(0.5)))
        self.assertIsNone(
            self.controller.process(
                {"gestureId": "other", "score": 1.0, "matched": True}
            )
        )

    def test_per_gesture_threshold_overrides_default_threshold(self):
        self.controller.configure(
            {"wave": "Space"},
            {"matchThreshold": 75, "cooldown": 0.5, "smoothing": 0},
            {"wave": 60},
        )
        match = self.match(0.65)
        match["matched"] = True

        self.assertEqual(self.controller.process(match)["action"], "press")

    def test_invalid_numeric_configuration_uses_safe_defaults(self):
        self.controller.configure(
            {"wave": "Space"},
            {
                "matchThreshold": "invalid",
                "cooldown": math.nan,
                "smoothing": None,
            },
            {"wave": math.nan},
        )

        self.assertEqual(
            self.controller.settings,
            {
                "matchThreshold": 75.0,
                "cooldown": 0.5,
                "smoothing": 2,
            },
        )
        self.assertEqual(self.controller.match_thresholds, {"wave": 75.0})

    def test_invalid_match_score_is_treated_as_no_match(self):
        action = self.controller.process(
            {"gestureId": "wave", "score": "invalid", "matched": True}
        )

        self.assertIsNone(action)


if __name__ == "__main__":
    unittest.main()
