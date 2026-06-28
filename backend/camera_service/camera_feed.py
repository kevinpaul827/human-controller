import cv2
import time

TARGET_FPS = 30
FRAME_DELAY = 1.0 / TARGET_FPS
DEF_CAMERA_INDEX = 0
WAIT_TIME = 10
QUIT_KEY = ord('q')

feed = cv2.VideoCapture(DEF_CAMERA_INDEX)
prev_frame_time = time.time()

while feed.isOpened():
    ret, frame = feed.read()
    if not ret:
        break
    
    current_time = time.time()
    elapsed_time = current_time - prev_frame_time

    if elapsed_time >= FRAME_DELAY:
        prev_frame_time = current_time
        
        cv2.imshow('Camera Feed', frame)

    if cv2.waitKey(WAIT_TIME) & 0xFF == QUIT_KEY:
        break

feed.release()
cv2.destroyAllWindows()