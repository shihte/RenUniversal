import cv2
import threading
import time
import numpy as np
from typing import Optional
from loguru import logger

class VideoStream:
    """
    負責從攝像頭抓取影像的線程安全類別。
    遵循 Pattern: Defensive Error Handling (Retry with Backoff)。
    """
    def __init__(self, src: int = 0, width: int = 1280, height: int = 720):
        self.src = src
        self.width = width
        self.height = height
        self.stream = cv2.VideoCapture(src)
        self._configure_stream()
        
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        self.lock = threading.Lock()
        
        if not self.grabbed:
            logger.warning(f"Initial frame grab failed for source {src}")

    def _configure_stream(self):
        """配置攝像頭參數。"""
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def start(self) -> "VideoStream":
        """啟動抓取執行緒。"""
        logger.info(f"Starting VideoStream on source {self.src}")
        t = threading.Thread(target=self.update, args=(), daemon=True)
        t.start()
        return self

    def update(self) -> None:
        """循環抓取最新影像，包含防禦性重連。"""
        retry_delay = 1.0
        max_delay = 30.0
        
        while not self.stopped:
            grabbed, frame = self.stream.read()
            
            if not grabbed:
                logger.error(f"Failed to grab frame from source {self.src}. Attempting reconnect in {retry_delay:.1f}s...")
                self.stream.release()
                time.sleep(retry_delay)
                
                # 指數退避 (Exponential Backoff)
                self.stream = cv2.VideoCapture(self.src)
                self._configure_stream()
                retry_delay = min(retry_delay * 2, max_delay)
                continue
            
            # 讀取成功，重置延遲
            retry_delay = 1.0
            
            with self.lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self) -> Optional[np.ndarray]:
        """讀取目前影像。"""
        with self.lock:
            return self.frame.copy() if self.grabbed and self.frame is not None else None

    def stop(self) -> None:
        """停止捕捉並釋放資源。"""
        logger.info(f"Stopping VideoStream on source {self.src}")
        self.stopped = True
        if self.stream.isOpened():
            self.stream.release()

    def is_opened(self) -> bool:
        """檢查串流是否正常開啟。"""
        return self.stream.isOpened()
