import sys

from PySide6.QtCore import QPoint, QSettings, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QLabel, QPushButton, QSizeGrip, QWidget

from .camera_overlay_widget import CameraOverlayWidget
from .logging_utils import log_info
from .platforms import configure_overlay_window, set_overlay_activation_policy


class PictureInPictureWindow(QWidget):
    visibilityChanged = Signal(bool)

    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("Human Controller Camera")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        if sys.platform == "darwin":
            self.setAttribute(
                Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow,
                True,
            )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMinimumSize(240, 160)
        self.resize(360, 240)
        self.setStyleSheet("background: black; border: 2px solid #f5b700;")

        self.preview = CameraOverlayWidget(self, smooth_pose=True)
        self.preview.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )

        self.close_button = QPushButton("×", self)
        self.close_button.setToolTip("Hide camera overlay")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setStyleSheet(
            "QPushButton { background: rgba(0, 0, 0, 190); color: white; "
            "border: 2px solid white; font-size: 20px; font-weight: bold; } "
            "QPushButton:hover { background: #d62828; }"
        )
        self.close_button.clicked.connect(self.hide_overlay)

        self.match_badge = QLabel(self)
        self.match_badge.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self.match_badge.setStyleSheet(
            "background: #f5b700; color: #111111; border: 2px solid #111111; "
            "padding: 6px 9px; font-size: 13px; font-weight: bold;"
        )
        self.match_badge.hide()
        self.match_timer = QTimer(self)
        self.match_timer.setSingleShot(True)
        self.match_timer.timeout.connect(self._hide_match_badge)
        self._triggered_match_visible = False

        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet("background: transparent; border: none;")

        self._drag_offset = QPoint()
        self._dragging = False
        self._placed_once = False
        self._native_overlay_configured = False
        self._settings = QSettings("Human Controller", "Human Controller")

        saved_geometry = self._settings.value("pictureInPicture/geometry")
        if saved_geometry is not None:
            self._placed_once = self.restoreGeometry(saved_geometry)

    def set_frame(self, image, timestamp_ms=None):
        self.preview.set_frame(image, timestamp_ms)

    def set_pose(self, payload):
        self.preview.set_pose(payload)

    def show_match(self, payload):
        if not payload:
            return

        key_action = payload.get("keyAction")
        if key_action == "reset":
            self._hide_match_badge()
            return
        if key_action == "release":
            key = str(payload.get("key") or "").strip()
            self._triggered_match_visible = False
            self.match_badge.setText(f"{key} released" if key else "Key released")
            self.match_badge.setStyleSheet(
                "background: #f5b700; color: #111111; border: 2px solid #111111; "
                "padding: 6px 9px; font-size: 13px; font-weight: bold;"
            )
            self.match_badge.adjustSize()
            self._position_match_badge()
            self.match_badge.show()
            self.match_badge.raise_()
            self.match_timer.start(700)
            return

        if not payload.get("matched"):
            return

        name = str(payload.get("name") or "Movement")
        if payload.get("triggered") or key_action == "press":
            key = str(payload.get("key") or "").strip()
            text = f"✓ {name}" + (f" → {key} DOWN" if key else "")
            self.match_badge.setStyleSheet(
                "background: #00c853; color: #07140b; border: 2px solid #07140b; "
                "padding: 6px 9px; font-size: 13px; font-weight: bold;"
            )
            self._triggered_match_visible = True
            duration_ms = None
        else:
            if self._triggered_match_visible:
                return
            text = f"Matched: {name}"
            self.match_badge.setStyleSheet(
                "background: #f5b700; color: #111111; border: 2px solid #111111; "
                "padding: 6px 9px; font-size: 13px; font-weight: bold;"
            )
            duration_ms = 900

        self.match_badge.setText(text)
        self.match_badge.adjustSize()
        self._position_match_badge()
        self.match_badge.show()
        self.match_badge.raise_()
        if duration_ms is None:
            self.match_timer.stop()
        else:
            self.match_timer.start(duration_ms)

    def clear(self):
        self.preview.clear_pose()
        self.preview.clear_frame()
        self.match_timer.stop()
        self._hide_match_badge()

    def _hide_match_badge(self):
        self._triggered_match_visible = False
        self.match_badge.hide()

    def _position_match_badge(self):
        self.match_badge.move(10, self.height() - self.match_badge.height() - 10)

    def show_overlay(self):
        if not self._placed_once:
            self._place_near_bottom_right()
            self._placed_once = True
        self.preview.show()
        activation_policy_configured = set_overlay_activation_policy(True)
        if sys.platform == "darwin" and not activation_policy_configured:
            log_info(
                "[overlay] warning: accessory activation policy failed; "
                "the session overlay may not appear above full-screen apps"
            )
        self.show()
        self._native_overlay_configured = False
        self._configure_native_overlay()
        QTimer.singleShot(0, self._finalize_native_overlay_configuration)
        self.raise_()
        self.visibilityChanged.emit(True)

    def _configure_native_overlay(self):
        if configure_overlay_window(self):
            self._native_overlay_configured = True

    def _finalize_native_overlay_configuration(self):
        if not self.isVisible():
            return
        self._configure_native_overlay()
        if sys.platform == "darwin" and not self._native_overlay_configured:
            log_info(
                "[overlay] warning: native always-on-top configuration failed; "
                "the session overlay may not appear above full-screen apps"
            )

    def hide_overlay(self):
        self._save_geometry()
        self.hide()
        set_overlay_activation_policy(False)
        self.visibilityChanged.emit(False)

    def shutdown(self):
        self._save_geometry()
        self.clear()
        self.hide()
        set_overlay_activation_policy(False)

    def _place_near_bottom_right(self):
        screen = QGuiApplication.screenAt(QCursor.pos())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        margin = 24
        self.move(
            available.right() - self.width() - margin,
            available.bottom() - self.height() - margin,
        )

    def _save_geometry(self):
        self._settings.setValue("pictureInPicture/geometry", self.saveGeometry())

    def resizeEvent(self, event):
        self.preview.setGeometry(self.rect())
        grip_size = self.size_grip.sizeHint()
        self.size_grip.setGeometry(
            self.width() - grip_size.width(),
            self.height() - grip_size.height(),
            grip_size.width(),
            grip_size.height(),
        )
        self.close_button.move(self.width() - self.close_button.width() - 8, 8)
        self._position_match_badge()
        self.preview.lower()
        self.close_button.raise_()
        self.match_badge.raise_()
        self.size_grip.raise_()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._save_geometry()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        self.hide_overlay()
        event.ignore()
