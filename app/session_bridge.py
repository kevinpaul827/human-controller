from PySide6.QtCore import QObject, Signal, Slot

class SessionBridge(QObject):
    sessionStatusChanged = Signal(dict)

    def __init__(self):
        super().__init__()
        self.state = "idle"

    def set_state(self, state):
        self.state = state
        self.sessionStatusChanged.emit({"state": self.state})

    @Slot()
    def startSession(self):
        self.set_state("starting")
    
    @Slot()
    def stopSession(self):
        self.set_state("idle")
