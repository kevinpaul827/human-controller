import unittest

from app.ui.overlay_constants import (
    connections_for_angle_joints,
    landmarks_for_angle_joints,
)
from backend.matching_engine.core.angles import AngleKey
from backend.pose_types import PoseKeypoint


class OverlayConstantsTests(unittest.TestCase):
    def test_landmarks_are_union_of_active_angle_triplets(self):
        landmarks = landmarks_for_angle_joints(
            [AngleKey.L_ELBOW.value, AngleKey.R_KNEE.value]
        )

        self.assertEqual(
            landmarks,
            {
                PoseKeypoint.L_SHOULDER,
                PoseKeypoint.L_ELBOW,
                PoseKeypoint.L_WRIST,
                PoseKeypoint.R_HIP,
                PoseKeypoint.R_KNEE,
                PoseKeypoint.R_ANKLE,
            },
        )

    def test_connections_draw_the_exact_angle_rays(self):
        connections = connections_for_angle_joints([AngleKey.L_ANKLE.value])

        self.assertEqual(
            connections,
            {
                (PoseKeypoint.L_KNEE, PoseKeypoint.L_ANKLE),
                (PoseKeypoint.L_ANKLE, PoseKeypoint.L_FOOT_INDEX),
            },
        )

    def test_unknown_joint_names_are_ignored(self):
        self.assertEqual(landmarks_for_angle_joints(["UNKNOWN"]), set())
        self.assertEqual(connections_for_angle_joints(["UNKNOWN"]), set())


if __name__ == "__main__":
    unittest.main()
