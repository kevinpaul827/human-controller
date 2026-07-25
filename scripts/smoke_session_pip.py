

import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from app.picture_in_picture_window import PictureInPictureWindow
from app.session_bridge import SessionBridge, SessionState


class FakeCamera(QObject):
    cameraStarted = Signal(str)
    cameraStopped = Signal(str)
    errorOccurred = Signal(str, str)
    frameProcessed = Signal(QImage, dict)
    previewFrameReady = Signal(QImage)
    gestureMatchUpdated = Signal(dict)
    previewAspectRatioChanged = Signal(float)

    def __init__(self):
        super().__init__()
        self.active_bridge = "session"


def main():
    app = QApplication([])
    camera = FakeCamera()
    bridge = SessionBridge(camera)
    picture_in_picture = PictureInPictureWindow()
    bridge.attach_picture_in_picture(picture_in_picture)
    bridge.state = SessionState.LIVE
    bridge.apply_overlay_visibility()

    frame = QImage(320, 240, QImage.Format.Format_RGB32)
    frame.fill(0xFF336699)
    camera.previewFrameReady.emit(frame)
    pose = {
        "detected": True,
        "landmarks": [[0.5, 0.5, 0.0] for _ in range(33)],
        "visibility": [1.0 for _ in range(33)],
    }
    camera.frameProcessed.emit(frame, pose)
    camera.gestureMatchUpdated.emit(
        {
            "gestureId": "wave",
            "name": "Wave",
            "score": 0.95,
            "matched": True,
            "triggered": True,
            "key": "Space",
        }
    )
    app.processEvents()

    assert picture_in_picture.isVisible()
    assert picture_in_picture.preview.isVisible()
    assert not picture_in_picture.preview._frame_image.isNull()
    assert picture_in_picture.preview._frame_image.pixelColor(0, 0).blue() > 0
    assert len(picture_in_picture.preview._landmarks) == 33
    assert picture_in_picture.match_badge.isVisible()
    assert picture_in_picture.match_badge.text() == "✓ Wave → Space"
    picture_in_picture.shutdown()
    print("SessionBridge -> visible PiP frame path passed")


if __name__ == "__main__":
    main()
