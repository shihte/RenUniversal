import cv2
import time

print("Testing camera 0 with CAP_AVFOUNDATION...")
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
time.sleep(1)
if not cap.isOpened():
    print("Camera 0 failed to open!")
else:
    ret, frame = cap.read()
    if ret:
        print("Camera 0 successfully read a frame!")
    else:
        print("Camera 0 opened, but failed to read a frame!")
    cap.release()
