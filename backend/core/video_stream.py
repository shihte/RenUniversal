import cv2
import threading
import time
from typing import Optional

class VideoStream:
    """
    負責從攝像頭抓取影像的線程安全類別。
    """
    def __init__(self, src: int = 0, width: int = 1280, height: int = 720):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 減少延遲
        
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        self.lock = threading.Lock()

    def start(self) -> "VideoStream":
        """啟動抓取執行緒。"""
        t = threading.Thread(target=self.update, args=(), daemon=True)
        t.start()
        return self

    def update(self) -> None:
        """循環抓取最新影像。"""
        while not self.stopped:
            grabbed, frame = self.stream.read()
            if not grabbed:
                self.stop()
                break
            
            with self.lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self) -> Optional[cv2.Mat]:
        """讀取目前影像。"""
        with self.lock:
            return self.frame.copy() if self.grabbed else None

    def stop(self) -> None:
        """停止捕捉並釋放資源。"""
        self.stopped = True
        if self.stream.isOpened():
            self.stream.release()

    def is_opened(self) -> bool:
        """檢查串流是否正常開啟。"""
        return self.stream.isOpened()
