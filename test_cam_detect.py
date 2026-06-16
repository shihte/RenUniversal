import cv2
import sys

def get_cameras():
    cameras = []
    # Test up to 5 indices
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                cameras.append(i)
            cap.release()
    return cameras

print("Detected cameras:", get_cameras())
