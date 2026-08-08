import unittest
import math

from app.trigger_controller import TriggerController


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
            {"matchThreshold": 75, "holdDuration": 1.0, "cooldown": 0.5, "smoothing": 0},
        )

    def match(self, score=0.9):
        return {
            "gestureId": "wave",
            "score": score,
            "matched": score >= 0.75,
        }

    def test_requires_hold_then_emits_key_down(self):
        self.assertIsNone(self.controller.process(self.match()))
        self.clock.advance(0.9)
        self.assertIsNone(self.controller.process(self.match()))
        self.clock.advance(0.1)

        action = self.controller.process(self.match())

        self.assertEqual(action["action"], "press")
        self.assertEqual(action["key"], "Space")

    def test_matched_gesture_holds_key_until_match_is_released(self):
        self.controller.process(self.match())
        self.clock.advance(1.0)
        self.assertEqual(self.controller.process(self.match())["action"], "press")
        self.clock.advance(2.0)
        self.assertIsNone(self.controller.process(self.match()))

        release = self.controller.process(
            {"gestureId": None, "score": 0, "matched": False}
        )

        self.assertEqual(release["action"], "release")
        self.assertEqual(release["key"], "Space")

    def test_motion_match_emits_one_short_tap_even_while_match_persists(self):
        match = self.match()
        match["gestureType"] = "motion"
        self.assertEqual(self.controller.process(match)["action"], "press")

        self.clock.advance(0.04)
        self.assertIsNone(self.controller.process(match))
        self.clock.advance(0.01)

        release = self.controller.process(match)

        self.assertEqual(release["action"], "release")
        self.assertEqual(release["key"], "Space")

        self.clock.advance(1.0)
        self.assertIsNone(self.controller.process(match))

    def test_motion_tap_rearms_only_after_match_clears(self):
        match = self.match()
        match["gestureType"] = "motion"
        self.controller.process(match)
        self.clock.advance(0.05)
        self.controller.process(match)
        self.assertIsNone(self.controller.process(match))

        self.controller.process({"gestureId": None, "score": 0, "matched": False})
        self.clock.advance(0.5)

        self.assertEqual(self.controller.process(match)["action"], "press")

    def test_can_press_again_after_release_and_cooldown(self):
        self.controller.process(self.match())
        self.clock.advance(1.0)
        self.controller.process(self.match())
        self.controller.process({"gestureId": None, "score": 0, "matched": False})
        self.clock.advance(0.05)
        self.controller.process({"gestureId": None, "score": 0, "matched": False})
        self.clock.advance(0.45)
        self.controller.process(self.match())
        self.clock.advance(1.0)

        self.assertEqual(self.controller.process(self.match())["action"], "press")

    def test_unbound_and_low_score_matches_do_not_trigger(self):
        self.controller.process(self.match(0.5))
        self.clock.advance(3.0)
        self.assertIsNone(self.controller.process(self.match(0.5)))
        self.assertIsNone(
            self.controller.process({"gestureId": "other", "score": 1.0, "matched": True})
        )

    def test_motion_match_emits_key_down_without_pose_hold_delay(self):
        match = self.match()
        match["gestureType"] = "motion"

        action = self.controller.process(match)

        self.assertEqual(action["action"], "press")
        self.assertEqual(action["key"], "Space")

    def test_per_gesture_threshold_overrides_default_threshold(self):
        self.controller.configure(
            {"wave": "Space"},
            {
                "matchThreshold": 75,
                "holdDuration": 1.0,
                "cooldown": 0.5,
                "smoothing": 0,
            },
            {"wave": 60},
        )
        match = self.match(0.65)
        match["matched"] = True

        self.assertIsNone(self.controller.process(match))
        self.clock.advance(1.0)

        self.assertEqual(self.controller.process(match)["action"], "press")

    def test_invalid_numeric_configuration_uses_safe_defaults(self):
        self.controller.configure(
            {"wave": "Space"},
            {
                "matchThreshold": "invalid",
                "holdDuration": math.inf,
                "cooldown": math.nan,
                "smoothing": None,
            },
            {"wave": math.nan},
        )

        self.assertEqual(
            self.controller.settings,
            {
                "matchThreshold": 75.0,
                "holdDuration": 1.5,
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
