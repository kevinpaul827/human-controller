import unittest

from PySide6.QtGui import QImage

from app.core.pose_pipeline import PosePipeline
from app.tests._bootstrap import ensure_qapplication


class PosePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = ensure_qapplication()

    def setUp(self):
        self.pipeline = PosePipeline()
        self.pipeline.processFrame.disconnect()
        self.addCleanup(self.pipeline.shutdown)

    def test_submit_allows_only_one_pending_frame(self):
        submitted = []
        self.pipeline.processFrame.connect(
            lambda frame, timestamp: submitted.append((frame, timestamp))
        )
        frame = QImage(2, 2, QImage.Format.Format_RGB32)

        self.assertTrue(self.pipeline.submit(frame, 123))
        self.assertFalse(self.pipeline.submit(frame, 456))
        self.pipeline.handle_processing_finished()
        self.assertTrue(self.pipeline.submit(frame, 456))

        self.assertEqual([timestamp for _, timestamp in submitted], [123, 456])

    def test_pose_result_keeps_the_matching_frame_and_timestamp(self):
        results = []
        self.pipeline.poseReady.connect(
            lambda pose, frame, timestamp: results.append((pose, frame, timestamp))
        )
        frame = QImage(2, 2, QImage.Format.Format_RGB32)

        self.pipeline.submit(frame, 789)
        pose = object()
        self.pipeline.handle_pose_estimated(pose)

        self.assertIs(results[0][0], pose)
        self.assertEqual(results[0][1].size(), frame.size())
        self.assertEqual(results[0][2], 789)


if __name__ == "__main__":
    unittest.main()
