"""
影像擷取技能邏輯 (Video Capture Skill Logic)
負責與攝像頭硬體交互，提供線程安全的影像串流。
"""

import cv2
import threading
import time
import numpy as np
from typing import Optional
from loguru import logger
from .schema import CaptureConfig, FrameData

class VideoCaptureSkill:
    """
    負責從攝像頭抓取影像的線程安全類別。
    
    該類別封裝了 OpenCV 的 VideoCapture，並提供自動重連與指標監控功能。
    遵循 Pattern: Tool Wrapper。
    """
    
    def __init__(self, config: CaptureConfig):
        """
        初始化擷取技能。
        
        Args:
            config (CaptureConfig): 擷取配置，包含來源索引與解析度設定。
        """
        self.config = config
        self.stream = cv2.VideoCapture(config.src)
        self._configure_stream()
        
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        self.lock = threading.Lock()
        
        if not self.grabbed:
            logger.warning(f"Initial frame grab failed for source {config.src}")

    def _configure_stream(self) -> None:
        """設定 OpenCV 攝像頭屬性。"""
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def start(self) -> "VideoCaptureSkill":
        """
        啟動背景抓取執行緒。
        
        Returns:
            VideoCaptureSkill: 自身實例以支援鏈式調用。
        """
        logger.info(f"Starting VideoCaptureSkill on source {self.config.src}")
        t = threading.Thread(target=self._capture_worker, args=(), daemon=True)
        t.start()
        return self

    def _capture_worker(self) -> None:
        """
        內部迴圈：持續從串流讀取最新影格。
        包含指數退避 (Exponential Backoff) 的自動重連邏輯。
        """
        retry_delay = 1.0
        max_delay = 30.0
        
        while not self.stopped:
            grabbed, frame = self.stream.read()
            
            if not grabbed:
                logger.error(f"Failed to grab frame from source {self.config.src}. Attempting reconnect in {retry_delay:.1f}s...")
                self.stream.release()
                time.sleep(retry_delay)
                
                # 重新初始化串流
                self.stream = cv2.VideoCapture(self.config.src)
                self._configure_stream()
                
                # 更新重試延遲
                retry_delay = min(retry_delay * 2, max_delay)
                continue
            
            # 讀取成功，重置延遲並更新影格
            retry_delay = 1.0
            with self.lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self) -> FrameData:
        """
        讀取目前緩衝區中的最新影格。
        
        Returns:
            FrameData: 包含抓取狀態與影像數據的強型別物件。
        """
        with self.lock:
            return FrameData(
                grabbed=self.grabbed,
                frame=self.frame.copy() if self.grabbed and self.frame is not None else None,
                timestamp=time.time()
            )

    def stop(self) -> None:
        """停止捕捉並釋放硬體資源。"""
        logger.info(f"Stopping VideoCaptureSkill on source {self.config.src}")
        self.stopped = True
        if self.stream.isOpened():
            self.stream.release()
