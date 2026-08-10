import tempfile
import unittest
from pathlib import Path

from backend.matching_engine import AngleKey

from app.core.gesture_session import GestureSession
from app.gestures.gesture_store import GestureStore


class FakeEvent:
    def to_dict(self):
        return {
            "gestureId": "wave",
            "name": "Wave",
            "score": 0.9,
            "timestamp": 1.0,
            "matched": True,
            "hasTemplates": True,
        }


class FakeMatcher:
    active_angle_keys = frozenset({AngleKey.L_ELBOW})
    bound_angle_keys = {AngleKey.L_ELBOW}

    def __init__(self):
        self.received_keys = None

    def angles_for_pose(self, _pose, keys):
        self.received_keys = keys
        return {AngleKey.L_ELBOW: 90.0}

    @staticmethod
    def match_pose(_pose, *, angles):
        return FakeEvent()


class FakeTriggerController:
    settings = {"matchThreshold": 75.0}

    @staticmethod
    def process(_payload):
        return {"action": "press", "key": "A"}

    @staticmethod
    def reset():
        pass


class FakeKeyInjector:
    def __init__(self):
        self.events = []

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))

    def release_all(self):
        self.events.append(("release_all",))


class GestureSessionTests(unittest.TestCase):
    def test_process_pose_matches_and_injects_only_for_a_live_session(self):
        matcher = FakeMatcher()
        injector = FakeKeyInjector()
        session = GestureSession(
            matcher=matcher,
            key_injector=injector,
            trigger_controller=FakeTriggerController(),
        )

        payload, angles = session.process_pose(
            object(),
            matcher.active_angle_keys,
            inject_keys=True,
        )

        self.assertEqual(angles, {AngleKey.L_ELBOW: 90.0})
        self.assertEqual(matcher.received_keys, matcher.active_angle_keys)
        self.assertEqual(payload["keyAction"], "press")
        self.assertTrue(payload["triggered"])
        self.assertEqual(injector.events, [("press", "A")])

    def test_configured_gestures_filter_matcher_templates_and_keep_bindings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = GestureStore(Path(temp_dir))
            store.create_motion(
                name="Wave",
                active_joints=["L_ELBOW"],
                trajectory=[{"L_ELBOW": 45.0}, {"L_ELBOW": 90.0}],
            )
            session = GestureSession(Path(temp_dir))

            mappings = session.configure_gestures(
                {"wave": "ArrowUp", "missing": "M"}
            )

            self.assertEqual(
                mappings,
                [{"gestureId": "wave", "name": "Wave", "key": "ArrowUp"}],
            )
            self.assertEqual(
                session.matcher.active_gesture_ids,
                frozenset({"wave", "missing"}),
            )

    def test_reset_payload_clears_the_live_match_state(self):
        self.assertEqual(
            GestureSession.reset_match_payload()["keyAction"],
            "reset",
        )


if __name__ == "__main__":
    unittest.main()
