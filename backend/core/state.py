import threading
import numpy as np
from typing import Optional
from loguru import logger
from .schema import DetectorStatus

class SharedState:
    """
    共享狀態類別，用於在不同線程間同步姿勢檢測結果與伺服器狀態。
    遵循 Pattern: Strongly Typed I/O 與 State Isolation。
    """
    def __init__(self):
        # 影像資料 (NDArray)
        self.frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        
        # Posture 狀態 (Pydantic Model)
        self.status = DetectorStatus()
        self.status_lock = threading.Lock()
        
        logger.info("SharedState initialized with Pydantic DetectorStatus schema")

    def update_status(self, **kwargs) -> None:
        """
        安全地更新狀態模型。
        使用 Pydantic model_copy 確保型別安全與不可變性。
        """
        with self.status_lock:
            # 建立目前狀態的字典，更新傳入的參數
            current_dict = self.status.model_dump()
            current_dict.update(kwargs)
            # 透過 Pydantic 驗證並建立新實例
            self.status = DetectorStatus(**current_dict)
            
    def get_status(self) -> DetectorStatus:
        """獲取目前狀態模型的快照。"""
        with self.status_lock:
            return self.status.model_copy()

    def update_frame(self, new_frame: np.ndarray) -> None:
        """安全地更新顯示幀。"""
        with self.frame_lock:
            self.frame = new_frame.copy()

    def get_frame(self) -> Optional[np.ndarray]:
        """獲取目前顯示幀副本。"""
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None
