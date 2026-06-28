from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtMultimedia import QCamera, QMediaDevices

class SessionBridge(QObject):
    sessionStatusChanged = Signal(dict)

    def __init__(self):
        super().__init__()
        self.state = "idle"
        self.active_camera = None

    def set_state(self, state):
        self.state = state
        self.sessionStatusChanged.emit({"state": self.state})

    def emit_error(self, message):
        self.state = "error"
        self.sessionStatusChanged.emit({"state": self.state, "message": message})

    def stop_camera(self):
        if self.active_camera is None:
            return
        
        self.active_camera.stop()
        self.active_camera.deleteLater()
        self.active_camera = None

    def show_webcam_feed(self):
        self.stop_camera()
    
        video_input = QMediaDevices.defaultVideoInput()

        if video_input.isNull():
            self.emit_error("No camera detected on this device.")
            return

        self.active_camera = QCamera(video_input)
        self.active_camera.activeChanged.connect(self.handle_active_changed)
        self.active_camera.errorOccurred.connect(self.handle_error_occurred)
        self.active_camera.start()

        # backend integration in later PR
 
    def handle_active_changed(self, active):
        if active:
            self.set_state("live")

    def handle_error_occurred(self, error, error_message):
        self.stop_camera()
        self.emit_error(error_message or "Unable to start camera session")

    @Slot()
    def startSession(self):
        if self.active_camera is not None:
            self.set_state("live")
            return

        self.set_state("starting")
        self.show_webcam_feed()

    @Slot()
    def stopSession(self):        
        self.stop_camera()
        self.set_state("idle")
