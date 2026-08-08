from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import Protocol

import cv2
import numpy as np

TARGET_FPS = 30
DEF_CAMERA_INDEX = 0
QUIT_KEY = ord('q')


class VideoCapture(Protocol):
    def isOpened(self) -> bool: ...

    def read(self) -> tuple[bool, np.ndarray | None]: ...

    def release(self) -> None: ...


class CameraFeed:
    def __init__(
        self,
        camera_index: int = DEF_CAMERA_INDEX,
        *,
        target_fps: float = TARGET_FPS,
        capture_factory: Callable[[int], VideoCapture] = cv2.VideoCapture,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if not math.isfinite(target_fps) or target_fps <= 0:
            raise ValueError("Target FPS must be a positive finite number.")
        self.camera_index = camera_index
        self.frame_delay = 1.0 / target_fps
        self._capture_factory = capture_factory
        self._clock = clock

        self.feed: VideoCapture | None = None
        self.prev_frame_time = 0.0
        self.start_time = 0.0
    
    def open(self) -> bool:
        if self.feed is not None and self.feed.isOpened():
            return True
        
        self.feed = self._capture_factory(self.camera_index)

        if not self.feed.isOpened():
            self.feed.release()
            self.feed = None
            return False
        
        self.start_time = self._clock()
        self.prev_frame_time = 0.0

        return True

    def read(self) -> tuple[bool, np.ndarray | None, int]:
        if self.feed is None or not self.feed.isOpened():
            return False, None, 0
        
        ret, frame = self.feed.read()

        if not ret:
            return False, None, 0
        
        current_time = self._clock()

        if current_time - self.prev_frame_time < self.frame_delay:
            return True, None, 0
        
        self.prev_frame_time = current_time
        timestamp_ms = int((current_time - self.start_time) * 1000)
        
        return True, frame, timestamp_ms
    
    def close(self) -> None:
        if self.feed is not None:
            self.feed.release()
            self.feed = None

def main():
    feed = CameraFeed()

    if not feed.open():
        return

    try:
        while True:
            ret, frame, _ = feed.read()
            if not ret:
                break

            if frame is not None:
                cv2.imshow("Camera Feed", frame)
            
            if cv2.waitKey(1) & 0xFF == QUIT_KEY:
                break
    finally:
        feed.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
