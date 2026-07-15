import numpy as np

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

from backend.perception.pose_estimator import PoseEstimator

class PoseProcessor(QObject):
    poseEstimated = Signal(object)
    processingFinished = Signal()
    errorOccurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.estimator = None

    @Slot(object, int)
    def process_frame(self, image, timestamp_ms):
        try:
            if not isinstance(image, QImage) or image.isNull():
                return

            if self.estimator is None:
                self.estimator = PoseEstimator()
            
            # PoseEstimator is based on logic that we are using an OpenCV camera
            # which uses BGR frames. The following lines of code is to transform
            # QImages into BGR frames to be accepted by PoseEstimator.
            image = image.convertToFormat(QImage.Format.Format_BGR888)
            
            width = image.width()
            height = image.height()
            bytes_per_line = image.bytesPerLine()

            frame = np.frombuffer(image.bits(), dtype=np.uint8, count=image.sizeInBytes())
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
        if self.estimator is not None:
            self.estimator.close()
            self.estimator = None
