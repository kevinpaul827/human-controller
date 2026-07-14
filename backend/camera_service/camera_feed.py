import cv2
import numpy as np
import time

TARGET_FPS = 30
FRAME_DELAY = 1.0 / TARGET_FPS
DEF_CAMERA_INDEX = 0
WAIT_TIME = 10
QUIT_KEY = ord('q')

class CameraFeed:
    def __init__(self, camera_index=DEF_CAMERA_INDEX):
        self.camera_index = camera_index
        self.frame_delay = FRAME_DELAY

        self.feed: cv2.VideoCapture | None = None
        self.prev_frame_time = 0.0
        self.start_time = 0.0
    
    def open(self) -> bool:
        if self.feed is not None and self.feed.isOpened():
            return True
        
        self.feed = cv2.VideoCapture(self.camera_index)

        if not self.feed.isOpened():
            self.feed.release()
            self.feed = None
            return False
        
        self.start_time = time.perf_counter()
        self.prev_frame_time = 0.0

        return True

    def read(self) -> tuple[bool, np.ndarray | None, int]:
        if self.feed is None or not self.feed.isOpened():
            return False, None, 0
        
        ret, frame = self.feed.read()

        if not ret:
            return False, None, 0
        
        current_time = time.perf_counter()

        if current_time - self.prev_frame_time < FRAME_DELAY:
            return True, None, 0
        
        self.prev_frame_time = current_time
        timestamp_ms = int((current_time - self.start_time) * 1000)
        
        return True, frame, timestamp_ms
    
    def close(self):
        if self.feed is not None:
            self.feed.release()
            self.feed = None

def main():
    feed = CameraFeed()

    if not feed.open():
        return

    try:
        while True:
            ret, frame, _ = frame.read()
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
