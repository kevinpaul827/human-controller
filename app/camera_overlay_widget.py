from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .logging_utils import log_debug, log_verbose
from .overlay_constants import (
    MIN_VISIBILITY,
    POSE_CONNECTIONS,
    connections_for_angle_joints,
    landmarks_for_angle_joints,
)

POINT_RADIUS = 4
LINE_WIDTH = 3
POSE_TRACKER_ALPHA = 0.55
POSE_TRACKER_BETA = 0.08
MAX_POSE_PROJECTION_MS = 33
POSE_TRACKER_RESET_GAP_MS = 250


class PoseOverlayTracker:
    """Smooth overlay landmarks without changing the pose used for matching."""

    def __init__(
        self,
        *,
        alpha=POSE_TRACKER_ALPHA,
        beta=POSE_TRACKER_BETA,
        max_projection_ms=MAX_POSE_PROJECTION_MS,
        reset_gap_ms=POSE_TRACKER_RESET_GAP_MS,
    ):
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.max_projection_ms = int(max_projection_ms)
        self.reset_gap_ms = int(reset_gap_ms)
        self.reset()

    def reset(self):
        self._landmarks = []
        self._positions = []
        self._velocities = []
        self._timestamp_ms = -1

    def update(self, landmarks, timestamp_ms):
        target = [
            [float(coordinate) for coordinate in landmark]
            for landmark in (landmarks or [])
        ]
        if not target:
            self.reset()
            return False

        timestamp_ms = int(timestamp_ms)
        should_reset = (
            not self._positions
            or len(target) != len(self._positions)
            or timestamp_ms < 0
            or self._timestamp_ms < 0
            or timestamp_ms - self._timestamp_ms > self.reset_gap_ms
        )
        if should_reset:
            self._landmarks = target
            self._positions = [landmark[:2] for landmark in target]
            self._velocities = [[0.0, 0.0] for _ in target]
            self._timestamp_ms = timestamp_ms
            return True

        elapsed_ms = timestamp_ms - self._timestamp_ms
        if elapsed_ms <= 0:
            return False

        elapsed_seconds = elapsed_ms / 1000.0
        positions = []
        velocities = []
        for index, landmark in enumerate(target):
            if len(landmark) < 2 or len(self._positions[index]) < 2:
                positions.append(landmark[:2])
                velocities.append([0.0, 0.0])
                continue

            landmark_position = []
            landmark_velocity = []
            for coordinate in range(2):
                projected = (
                    self._positions[index][coordinate]
                    + self._velocities[index][coordinate] * elapsed_seconds
                )
                residual = landmark[coordinate] - projected
                landmark_position.append(projected + self.alpha * residual)
                landmark_velocity.append(
                    self._velocities[index][coordinate]
                    + self.beta * residual / elapsed_seconds
                )
            positions.append(landmark_position)
            velocities.append(landmark_velocity)

        self._landmarks = target
        self._positions = positions
        self._velocities = velocities
        self._timestamp_ms = timestamp_ms
        return True

    def sample(self, timestamp_ms=None):
        if not self._landmarks:
            return []

        projection_ms = 0
        if timestamp_ms is not None and self._timestamp_ms >= 0:
            projection_ms = min(
                self.max_projection_ms,
                max(0, int(timestamp_ms) - self._timestamp_ms),
            )
        projection_seconds = projection_ms / 1000.0

        result = []
        for index, landmark in enumerate(self._landmarks):
            rendered = list(landmark)
            for coordinate in range(min(2, len(rendered))):
                value = (
                    self._positions[index][coordinate]
                    + self._velocities[index][coordinate] * projection_seconds
                )
                rendered[coordinate] = min(1.0, max(0.0, value))
            result.append(rendered)
        return result


class CameraOverlayWidget(QWidget):
    def __init__(self, parent=None, *, smooth_pose=False):
        super().__init__(parent)
        self._frame_image = QImage()
        self._draw_rect = QRectF()
        self._landmarks = []
        self._visibility = []
        self._render_joints = None
        self._smooth_pose = bool(smooth_pose)
        self._pose_tracker = PoseOverlayTracker()
        self._preview_timestamp_ms = -1
        self._frame_log_emitted = False
        self._paint_log_emitted = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.hide()

    def set_frame(self, image, timestamp_ms=None):
        if not isinstance(image, QImage) or image.isNull():
            self._frame_image = QImage()
            self._draw_rect = QRectF()
            self.update()
            return
        self._frame_image = image.mirrored(True, False)
        if timestamp_ms is not None:
            self._preview_timestamp_ms = int(timestamp_ms)
            if self._smooth_pose:
                self._landmarks = self._pose_tracker.sample(
                    self._preview_timestamp_ms
                )
        if not self._frame_log_emitted:
            log_debug(f"[overlay] received first synced frame {image.width()}x{image.height()}")
            self._frame_log_emitted = True
        self.update()

    def set_pose(self, payload):
        if not payload or not payload.get("detected"):
            log_verbose("[overlay] cleared pose payload")
            self._landmarks = []
            self._visibility = []
            self._render_joints = None
            self._pose_tracker.reset()
            self.update()
            return

        landmarks = payload.get("landmarks")
        visibility = payload.get("visibility")
        target_landmarks = [
            [float(coordinate) for coordinate in landmark]
            for landmark in (landmarks if landmarks is not None else [])
        ]
        target_visibility = [
            float(value) for value in (visibility if visibility is not None else [])
        ]
        self._render_joints = (
            tuple(payload.get("renderJoints", []))
            if "renderJoints" in payload
            else None
        )
        timestamp_ms = int(payload.get("timestampMs", -1))
        if self._smooth_pose:
            self._pose_tracker.update(target_landmarks, timestamp_ms)
            self._landmarks = self._pose_tracker.sample(
                self._preview_timestamp_ms
                if self._preview_timestamp_ms >= 0
                else timestamp_ms
            )
        else:
            self._landmarks = target_landmarks
        self._visibility = target_visibility

        count = len(target_landmarks)
        log_verbose(f"[overlay] received pose payload with {count} landmarks")
        self.update()

    def clear_pose(self):
        log_debug("[overlay] clearing stored landmarks")
        self._landmarks = []
        self._visibility = []
        self._render_joints = None
        self._pose_tracker.reset()
        self.update()

    def clear_frame(self):
        log_debug("[overlay] clearing stored frame")
        self._frame_image = QImage()
        self._draw_rect = QRectF()
        self._frame_log_emitted = False
        self._paint_log_emitted = False
        self._preview_timestamp_ms = -1
        self._pose_tracker.reset()
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

        connections = (
            POSE_CONNECTIONS
            if self._render_joints is None
            else connections_for_angle_joints(self._render_joints)
        )
        for start_idx, end_idx in connections:
            start_point = self._point_for_index(start_idx)
            end_point = self._point_for_index(end_idx)
            if start_point is None or end_point is None:
                continue
            painter.drawLine(QLineF(*start_point, *end_point))

        point_pen = QPen(QColor(255, 255, 255, 220))
        point_pen.setWidth(2)
        painter.setPen(point_pen)
        painter.setBrush(QColor(86, 255, 176, 230))

        landmarks = (
            range(len(self._landmarks))
            if self._render_joints is None
            else landmarks_for_angle_joints(self._render_joints)
        )
        for index in landmarks:
            point = self._point_for_index(index)
            if point is None:
                continue
            painter.drawEllipse(QPointF(*point), POINT_RADIUS, POINT_RADIUS)

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

        x = draw_rect.left() + (1.0 - landmark_x) * draw_rect.width()
        y = draw_rect.top() + landmark_y * draw_rect.height()
        x = min(max(x, min_x), max_x)
        y = min(max(y, min_y), max_y)
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
