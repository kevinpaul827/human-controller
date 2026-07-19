from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .logging_utils import log_debug, log_verbose
from .overlay_constants import MIN_VISIBILITY, POSE_CONNECTIONS

POINT_RADIUS = 4
LINE_WIDTH = 3


class CameraOverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._frame_image = QImage()
        self._draw_rect = QRectF()
        self._landmarks = []
        self._visibility = []
        self._frame_log_emitted = False
        self._paint_log_emitted = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.hide()

    def set_frame(self, image):
        if not isinstance(image, QImage) or image.isNull():
            self._frame_image = QImage()
            self._draw_rect = QRectF()
            self.update()
            return

        self._frame_image = image
        if not self._frame_log_emitted:
            log_debug(f"[overlay] received first synced frame {image.width()}x{image.height()}")
            self._frame_log_emitted = True
        self.update()

    def set_pose(self, payload):
        if not payload or not payload.get("detected"):
            log_verbose("[overlay] cleared pose payload")
            self._landmarks = []
            self._visibility = []
            self.update()
            return

        landmarks = payload.get("landmarks")
        visibility = payload.get("visibility")
        self._landmarks = landmarks if landmarks is not None else []
        self._visibility = visibility if visibility is not None else []
        count = len(self._landmarks)
        log_verbose(f"[overlay] received pose payload with {count} landmarks")
        self.update()

    def clear_pose(self):
        log_debug("[overlay] clearing stored landmarks")
        self._landmarks = []
        self._visibility = []
        self.update()

    def clear_frame(self):
        log_debug("[overlay] clearing stored frame")
        self._frame_image = QImage()
        self._draw_rect = QRectF()
        self._frame_log_emitted = False
        self._paint_log_emitted = False
        self.update()

    def paintEvent(self, _event):
        if self.width() <= 0 or self.height() <= 0:
            log_debug(f"[overlay] paint skipped because widget size is {self.width()}x{self.height()}")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if not self._frame_image.isNull():
            self._draw_rect = self._aspect_fit_rect()
            painter.drawImage(self._draw_rect, self._frame_image)
        else:
            self._draw_rect = QRectF()

        if len(self._landmarks) == 0:
            if not self._paint_log_emitted:
                log_debug("[overlay] paint has frame but no landmarks yet")
                self._paint_log_emitted = True
            return

        if not self._paint_log_emitted:
            log_debug(f"[overlay] painting {len(self._landmarks)} landmarks at {self.width()}x{self.height()}")
            self._paint_log_emitted = True

        if self._draw_rect.isNull():
            return

        # Keep pose strokes inside the letterboxed preview area so they do not
        # bleed into the black margins when landmarks land near the frame edge.
        painter.save()
        painter.setClipRect(self._draw_rect)

        line_pen = QPen(QColor(86, 255, 176, 210))
        line_pen.setWidth(LINE_WIDTH)
        painter.setPen(line_pen)

        for start_idx, end_idx in POSE_CONNECTIONS:
            start_point = self._point_for_index(start_idx)
            end_point = self._point_for_index(end_idx)
            if start_point is None or end_point is None:
                continue
            painter.drawLine(*start_point, *end_point)

        point_pen = QPen(QColor(255, 255, 255, 220))
        point_pen.setWidth(2)
        painter.setPen(point_pen)
        painter.setBrush(QColor(86, 255, 176, 230))

        for index in range(len(self._landmarks)):
            point = self._point_for_index(index)
            if point is None:
                continue
            x, y = point
            painter.drawEllipse(x - POINT_RADIUS, y - POINT_RADIUS, POINT_RADIUS * 2, POINT_RADIUS * 2)

        painter.restore()

    def _point_for_index(self, index):
        if index >= len(self._landmarks):
            return None

        if index < len(self._visibility) and self._visibility[index] < MIN_VISIBILITY:
            return None

        landmark = self._landmarks[index]
        if len(landmark) < 2:
            return None

        landmark_x = float(landmark[0])
        landmark_y = float(landmark[1])
        if not 0.0 <= landmark_x <= 1.0 or not 0.0 <= landmark_y <= 1.0:
            return None

        draw_rect = self._draw_rect if not self._draw_rect.isNull() else QRectF(self.rect())
        inset = POINT_RADIUS + max(1, LINE_WIDTH // 2)
        min_x = draw_rect.left() + inset
        max_x = draw_rect.right() - inset
        min_y = draw_rect.top() + inset
        max_y = draw_rect.bottom() - inset

        if max_x < min_x or max_y < min_y:
            return None

        x = draw_rect.left() + landmark_x * draw_rect.width()
        y = draw_rect.top() + landmark_y * draw_rect.height()
        x = round(min(max(x, min_x), max_x))
        y = round(min(max(y, min_y), max_y))
        return x, y

    def _aspect_fit_rect(self):
        if self._frame_image.isNull() or self.width() <= 0 or self.height() <= 0:
            return QRectF()

        frame_width = self._frame_image.width()
        frame_height = self._frame_image.height()
        if frame_width <= 0 or frame_height <= 0:
            return QRectF()

        scale = min(self.width() / frame_width, self.height() / frame_height)
        draw_width = frame_width * scale
        draw_height = frame_height * scale
        left = (self.width() - draw_width) / 2
        top = (self.height() - draw_height) / 2
        return QRectF(left, top, draw_width, draw_height)
