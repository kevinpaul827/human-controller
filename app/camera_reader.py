import threading

from PySide6.QtCore import QObject, Signal, Slot

from backend.camera_service.camera_feed import CameraFeed

class CameraReader(QObject):
    frameReady = Signal(object, int)
    cameraStopped = Signal()
    errorOccurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.feed = CameraFeed()
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    @Slot()
    def run(self):
        self.stop_event.clear()

        if not self.feed.open():
            self.errorOccurred.emit("Could not open camera.")
            self.cameraStopped.emit()
            return

        try:
            while not self.stop_event.is_set():
                ret, frame, timestamp_ms = self.feed.read()

                if not ret:
                    self.errorOccurred.emit("Failed to read frame")
                    break

                if frame is None:
                    continue

                self.frameReady.emit(frame, timestamp_ms)

        except Exception as error_msg:
            self.errorOccurred.emit(str(error_msg))
            
        finally:
            self.feed.close()
            self.cameraStopped.emit()
