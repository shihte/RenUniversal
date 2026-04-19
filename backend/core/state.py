from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import threading
import numpy as np

@dataclass
class SharedState:
    """
    共享狀態類別，用於在不同線程間同步姿勢檢測結果與伺服器狀態。
    遵循強型別與狀態隔離模式。
    """
    # 影像資料 (NDArray)
    frame: Optional[np.ndarray] = None
    frame_lock: threading.Lock = field(default_factory=threading.Lock)
    
    # Posture 狀態
    status: Dict[str, Any] = field(default_factory=lambda: {
        "ratio": 0,
        "nose_chin_ratio": 0,
        "is_bad_posture": False,
        "down_count": 0,
        "fps": 0,
        "connected": False,
        "calibrating": True,
        "calibration_progress": 0,
        "is_turning": False,
        "baseline_eye_dist": 0,
        "threshold": 30.0,
        "yaw_tolerance": 20.0,
        "is_active": True,
        "latency_ms": 0
    })
    status_lock: threading.Lock = field(default_factory=threading.Lock)
    
    def update_status(self, new_data: Dict[str, Any]) -> None:
        """安全地更新狀態字典。"""
        with self.status_lock:
            self.status.update(new_data)
            
    def get_status(self) -> Dict[str, Any]:
        """獲取目前狀態副本。"""
        with self.status_lock:
            return self.status.copy()

    def update_frame(self, new_frame: np.ndarray) -> None:
        """安全地更新顯示幀。"""
        with self.frame_lock:
            self.frame = new_frame.copy()

    def get_frame(self) -> Optional[np.ndarray]:
        """獲取目前顯示幀副本。"""
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None
