import numpy as np

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

from backend.perception.models import DEFAULT_POSE_MODEL, normalize_pose_model
from backend.perception.pose_estimator import PoseEstimator


class PoseProcessor(QObject):
    poseEstimated = Signal(object)
    processingFinished = Signal()
    errorOccurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.model = DEFAULT_POSE_MODEL
        self.estimator = None

    @Slot(str)
    def configure_model(self, model):
        resolved_model = normalize_pose_model(model)
        if resolved_model == self.model:
            return
        estimator = self.estimator
        self.estimator = None
        self.model = resolved_model
        if estimator is None:
            return
        try:
            estimator.close()
        except Exception as error_msg:
            self.errorOccurred.emit(str(error_msg))

    @Slot(object, int)
    def process_frame(self, image, timestamp_ms):
        try:
            if not isinstance(image, QImage) or image.isNull():
                return

            if self.estimator is None:
                self.estimator = PoseEstimator(self.model)

            image = image.convertToFormat(QImage.Format.Format_BGR888)

            width = image.width()
            height = image.height()
            bytes_per_line = image.bytesPerLine()

            frame = np.frombuffer(
                image.bits(),
                dtype=np.uint8,
                count=image.sizeInBytes(),
            )
            frame = frame.reshape(height, bytes_per_line)
            frame = frame[:, : width * 3].reshape(height, width, 3)
            frame = np.ascontiguousarray(frame)

            pose = self.estimator.estimate_pose(frame, timestamp_ms)
            self.poseEstimated.emit(pose)

        except Exception as error_msg:
            self.errorOccurred.emit(str(error_msg))

        finally:
            self.processingFinished.emit()

    @Slot()
    def close(self):
        estimator = self.estimator
        self.estimator = None
        if estimator is not None:
            estimator.close()
