import unittest

from app.gesture_regions import infer_gesture_regions


class GestureRegionInferenceTests(unittest.TestCase):
    def test_infers_upper_body_for_arm_joints(self) -> None:
        self.assertEqual(
            infer_gesture_regions(["L_ELBOW", "L_SHOULDER_ABD"]),
            ["upper_body"],
        )

    def test_infers_lower_body_for_leg_joints(self) -> None:
        self.assertEqual(
            infer_gesture_regions(["L_HIP", "R_KNEE"]),
            ["lower_body"],
        )

    def test_infers_both_regions_for_mixed_joint_sets(self) -> None:
        self.assertEqual(
            infer_gesture_regions(["L_ELBOW", "R_ANKLE"]),
            ["upper_body", "lower_body"],
        )


if __name__ == "__main__":
    unittest.main()
