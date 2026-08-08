import unittest

from app.ui.camera_overlay_widget import PoseOverlayTracker


class PoseOverlayTrackerTests(unittest.TestCase):
    def test_tracker_dampens_stationary_jitter(self) -> None:
        tracker = PoseOverlayTracker()
        outputs = []
        for index, value in enumerate([0.497, 0.503] * 20):
            timestamp_ms = index * 33
            tracker.update([[value, 0.5, -0.1]], timestamp_ms)
            outputs.append(tracker.sample(timestamp_ms)[0][0])

        self.assertLess(max(outputs[-10:]) - min(outputs[-10:]), 0.004)

    def test_tracker_follows_constant_motion_with_short_projection(self) -> None:
        tracker = PoseOverlayTracker()
        for index in range(12):
            timestamp_ms = index * 33
            x = 0.2 + 0.0004 * timestamp_ms
            tracker.update([[x, 0.5, -0.1]], timestamp_ms)

        projected = tracker.sample(timestamp_ms + 33)
        expected_x = 0.2 + 0.0004 * (timestamp_ms + 33)
        self.assertAlmostEqual(projected[0][0], expected_x, delta=0.01)

    def test_projection_is_capped_to_one_camera_frame(self) -> None:
        tracker = PoseOverlayTracker()
        tracker.update([[0.4, 0.5]], 100)
        tracker.update([[0.5, 0.5]], 133)

        self.assertEqual(tracker.sample(166), tracker.sample(333))

    def test_duplicate_or_backward_timestamp_is_ignored(self) -> None:
        tracker = PoseOverlayTracker()
        tracker.update([[0.4, 0.5]], 100)
        before = tracker.sample(100)

        self.assertFalse(tracker.update([[0.9, 0.5]], 100))
        self.assertFalse(tracker.update([[0.9, 0.5]], 90))
        self.assertEqual(tracker.sample(100), before)

    def test_long_gap_and_landmark_count_change_reset_tracker(self) -> None:
        tracker = PoseOverlayTracker()
        tracker.update([[0.4, 0.5]], 100)
        tracker.update([[0.6, 0.5]], 400)
        self.assertEqual(tracker.sample(400)[0][:2], [0.6, 0.5])

        tracker.update([[0.3, 0.4], [0.7, 0.8]], 433)
        self.assertEqual(
            [landmark[:2] for landmark in tracker.sample(433)],
            [[0.3, 0.4], [0.7, 0.8]],
        )

    def test_sample_clamps_screen_coordinates(self) -> None:
        tracker = PoseOverlayTracker()
        tracker.update([[-0.1, 1.2, 0.0]], 100)

        self.assertEqual(tracker.sample(100)[0][:2], [0.0, 1.0])


if __name__ == "__main__":
    unittest.main()
