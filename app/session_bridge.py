from PySide6.QtCore import QCameraPermission, QCoreApplication, QObject, Qt, Signal, Slot

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
    
    def check_camera_permissions(self):
        app = QCoreApplication.instance()
        permission = QCameraPermission()

        status = app.checkPermission(permission)

        if status == Qt.PermissionStatus.Granted:
            return True
        elif status == Qt.PermissionStatus.Denied:
            self.emit_error("Camera permission denied")
            return False

        app.requestPermission(permission, self, self.handle_request_camera)

        return False

    def show_camera_feed(self):
        from PySide6.QtMultimedia import QCamera, QMediaDevices

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
    
    def stop_camera(self):
        if self.active_camera is None:
            return
        
        self.active_camera.stop()
        self.active_camera.deleteLater()
        self.active_camera = None
    
    def handle_request_camera(self, permission):
        app = QCoreApplication.instance()

        if app.checkPermission(permission) == Qt.PermissionStatus.Granted:
            self.show_camera_feed()
        else:
            self.emit_error("Camera permission denied")
 
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

        if self.check_camera_permissions():
            self.show_camera_feed()

    @Slot()
    def stopSession(self):        
        self.stop_camera()
        self.set_state("idle")
