"""app/bridges/bridge_common.py

Shared helper for CalibrateBridge and SessionBridge
preview/state handling."
"""

from __future__ import annotations

from .bridge_types import PosePayload


class CameraBridgeBase:
    def _init_camera_preview_bridge(self, camera_manager, initial_state) -> None:
        """Initialize camera preview bridge"""
        self.state = initial_state
        self.preview_widget = None
        self.preview_bounds = (0, 0, 0, 0)
        self.camera = camera_manager

    def _emit_status_payload(self, payload: dict) -> None:
        """Emit the bridge-specific status signal payload."""
        raise NotImplementedError

    def _after_state_change(self) -> None:
        """Run bridge-specific side effects after state updates."""
        pass

    def _handle_live_pose(self, pose: PosePayload) -> None:
        """Handle extra bridge-specific work for each live pose update."""
        pass

    def _clear_extra_preview(self) -> None:
        """Clear any bridge-specific preview surface beyond the shared widget."""
        pass

    def check_camera_ownership(self) -> bool:
        """Check if bridge currently owns the shared camera."""
        return self.camera.active_bridge == self.BRIDGE

    def attach_preview_widget(self, preview_widget) -> None:
        """Attach the preview widget managed by the bridge."""
        self.preview_widget = preview_widget
        self.preview_widget.hide()

    def set_state(self, state) -> None:
        """Update the state of the bridge."""
        self.state = state
        self._emit_status_payload({"state": self.state.value})
        self._after_state_change()

    def emit_error(self, message: str) -> None:
        """Update state of bridge to 'error' and clear preview."""
        self.state = self.ERROR_STATE
        self._emit_status_payload({"state": self.state.value, "message": message})
        self.clear_preview()
        self._after_state_change()

    def apply_preview_bounds(self) -> None:
        """Apply current preview bounds and update widget visiblity."""
        if self.preview_widget is None:
            return

        left, top, width, height = self.preview_bounds
        self.previewBoundsChanged.emit(left, top, width, height)

        if self._should_show_preview(width, height):
            self.preview_widget.show()
            self.preview_widget.raise_()
            return

        self.preview_widget.hide()

    def clear_preview(self) -> None:
        """Hide and clear camera preview."""
        if self.preview_widget is not None:
            self.preview_widget.hide()
            self.preview_widget.clear_pose()
            self.preview_widget.clear_frame()
        self._clear_extra_preview()

    def update_preview_bounds(self, left, top, width, height) -> None:
        """Store properties of preview bounds and apply them."""
        self.preview_bounds = (
            max(0, round(left)),
            max(0, round(top)),
            max(0, round(width)),
            max(0, round(height)),
        )
        self.apply_preview_bounds()

    def handle_camera_started(self, bridge) -> None:
        """Set camera to 'live' on camera start."""
        if bridge != self.BRIDGE:
            return

        self.set_state(self.LIVE_STATE)
        self.apply_preview_bounds()

    def handle_camera_stopped(self, bridge) -> None:
        """Set camera to 'idle' on camera stop."""
        if bridge != self.BRIDGE:
            return

        self.set_state(self.IDLE_STATE)
        self.clear_preview()

    def handle_camera_error(self, message, bridge) -> None:
        """Handle when there is a camera error."""
        if bridge != self.BRIDGE:
            return

        self.emit_error(message)

    def handle_frame_processed(self, frame, pose) -> None:
        """Forward a processed frame amd pose while live."""
        if not self.check_camera_ownership():
            return

        if self.state != self.LIVE_STATE:
            return

        if self.preview_widget is not None:
            self.preview_widget.set_frame(frame)

        self._handle_live_pose(pose)
        self.poseEstimated.emit(pose)

    def handle_preview_aspect_ratio_changed(self, aspect_ratio) -> None:
        """Forward preview aspect-ratio changes."""
        if not self.check_camera_ownership():
            return

        self.previewAspectRatioChanged.emit(aspect_ratio)

    def _should_show_preview(self, width: int, height: int) -> bool:
        """Check if the preview widget should be currently visible."""
        return (
            self.state == self.LIVE_STATE
            and width > 0
            and height > 0
            and self.check_camera_ownership()
        )
