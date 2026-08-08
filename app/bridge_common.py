from __future__ import annotations


class CameraBridgeBase:
    """Shared helper for CalibrateBridge and SessionBridge preview/state handling."""

    def _init_camera_preview_bridge(self, camera_manager, initial_state) -> None:
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

    def _handle_live_pose(self, pose: dict) -> None:
        """Handle extra bridge-specific work for each live pose update."""
        pass

    def _clear_extra_preview(self) -> None:
        """Clear any bridge-specific preview surface beyond the shared widget."""
        pass

    def check_camera_ownership(self) -> bool:
        return self.camera.active_bridge == self.BRIDGE

    def attach_preview_widget(self, preview_widget) -> None:
        self.preview_widget = preview_widget
        self.preview_widget.hide()

    def set_state(self, state) -> None:
        self.state = state
        self._emit_status_payload({"state": self.state.value})
        self._after_state_change()

    def emit_error(self, message: str) -> None:
        self.state = self.ERROR_STATE
        self._emit_status_payload({"state": self.state.value, "message": message})
        self.clear_preview()
        self._after_state_change()

    def apply_preview_bounds(self) -> None:
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
        if self.preview_widget is not None:
            self.preview_widget.hide()
            self.preview_widget.clear_pose()
            self.preview_widget.clear_frame()
        self._clear_extra_preview()

    def handle_camera_started(self, bridge) -> None:
        if bridge != self.BRIDGE:
            return

        self.set_state(self.LIVE_STATE)
        self.apply_preview_bounds()

    def handle_camera_stopped(self, bridge) -> None:
        if bridge != self.BRIDGE:
            return

        self.set_state(self.IDLE_STATE)
        self.clear_preview()

    def handle_camera_error(self, message, bridge) -> None:
        if bridge != self.BRIDGE:
            return

        self.emit_error(message)

    def handle_frame_processed(self, frame, pose) -> None:
        if not self.check_camera_ownership():
            return

        if self.state != self.LIVE_STATE:
            return

        if self.preview_widget is not None:
            self.preview_widget.set_frame(frame)

        self._handle_live_pose(pose)
        self.poseEstimated.emit(pose)

    def handle_preview_aspect_ratio_changed(self, aspect_ratio) -> None:
        if not self.check_camera_ownership():
            return

        self.previewAspectRatioChanged.emit(aspect_ratio)

    def update_preview_bounds(self, left, top, width, height) -> None:
        self.preview_bounds = (
            max(0, round(left)),
            max(0, round(top)),
            max(0, round(width)),
            max(0, round(height)),
        )
        self.apply_preview_bounds()

    def _should_show_preview(self, width: int, height: int) -> bool:
        return (
            self.state == self.LIVE_STATE
            and width > 0
            and height > 0
            and self.check_camera_ownership()
        )
