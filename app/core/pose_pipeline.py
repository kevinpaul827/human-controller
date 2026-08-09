from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QImage

from .pose_processor import PoseProcessor


class PosePipeline(QObject):
    poseReady = Signal(object, QImage, int)
    errorOccurred = Signal(str)
    processFrame = Signal(object, int)
    configurePoseModel = Signal(str)
    closeProcessor = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processing = False
        self._pending_frame = QImage()
        self._pending_timestamp_ms = -1
        self.thread = QThread(self)
        self.processor = PoseProcessor()
        self.processor.moveToThread(self.thread)

        self.processFrame.connect(
            self.processor.process_frame,
            Qt.ConnectionType.QueuedConnection,
        )
        self.configurePoseModel.connect(
            self.processor.configure_model,
            Qt.ConnectionType.QueuedConnection,
        )
        self.processor.poseEstimated.connect(self.handle_pose_estimated)
        self.processor.processingFinished.connect(self.handle_processing_finished)
        self.processor.errorOccurred.connect(self.errorOccurred)

        self.closeProcessor.connect(
            self.processor.close,
            Qt.ConnectionType.BlockingQueuedConnection,
        )
        self.thread.finished.connect(self.processor.deleteLater)
        self.thread.start()

    def submit(self, image: QImage, timestamp_ms: int) -> bool:
        if self._processing:
            return False
        self._pending_frame = image.copy()
        self._pending_timestamp_ms = int(timestamp_ms)
        self._processing = True
        self.processFrame.emit(self._pending_frame.copy(), self._pending_timestamp_ms)
        return True

    def configure_model(self, model_name: str) -> None:
        self.configurePoseModel.emit(model_name)

    def clear_pending(self) -> None:
        self._pending_frame = QImage()
        self._pending_timestamp_ms = -1

    def shutdown(self) -> None:
        self.clear_pending()
        if self.thread.isRunning():
            self.closeProcessor.emit()
            self.thread.quit()
            self.thread.wait()

    def handle_pose_estimated(self, pose) -> None:
        if self._pending_frame.isNull():
            return
        frame = self._pending_frame
        timestamp_ms = self._pending_timestamp_ms
        self.clear_pending()
        self.poseReady.emit(pose, frame, timestamp_ms)

    def handle_processing_finished(self) -> None:
        self._processing = False
