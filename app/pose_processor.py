from PySide6.QtCore import QObject, Signal, Slot

from backend.perception.pose_estimator import PoseEstimator

class PoseProcessor(QObject):
    poseEstimated = Signal(object)
    processingFinished = Signal()
    errorOccurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.estimator = None

    @Slot(object, int)
    def process_frame(self, frame, timestamp_ms):
        try:
            if self.estimator is None:
                self.estimator = PoseEstimator()

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
