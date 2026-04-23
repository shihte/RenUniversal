import threading
import numpy as np
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger
from .schema import DetectorStatus

class SharedState:
    """
    共享狀態類別，具備個人化偏好記憶能力。
    Pattern: State Isolation & Persistence (Memory)
    """
    def __init__(self, prefs_path: str = "preferences.json"):
        self.prefs_path = Path(prefs_path)
        
        # 影像資料
        self.frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        
        # Posture 狀態
        self.status = DetectorStatus()
        self.status_lock = threading.Lock()
        
        # 個人化偏好 (Memory)
        self.prefs = self._load_prefs()
        
        logger.info(f"SharedState initialized. Memory loaded from {prefs_path}")

    def _load_prefs(self) -> Dict[str, Any]:
        """從本地檔案載入使用者偏好。"""
        default_prefs = {
            "threshold_ratio": 0.20,
            "yaw_tolerance": 0.10,
            "username": "User",
            "last_baseline_eye": 0.0
        }
        if self.prefs_path.exists():
            try:
                with open(self.prefs_path, "r") as f:
                    return {**default_prefs, **json.load(f)}
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
        return default_prefs

    def save_prefs(self, new_prefs: Dict[str, Any]) -> None:
        """持久化儲存使用者偏好。"""
        self.prefs.update(new_prefs)
        try:
            with open(self.prefs_path, "w") as f:
                json.dump(self.prefs, f, indent=4)
            logger.info("Preferences saved successfully (Personalization)")
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")

    def update_status(self, **kwargs) -> None:
        with self.status_lock:
            current_dict = self.status.model_dump()
            current_dict.update(kwargs)
            self.status = DetectorStatus(**current_dict)
            
    def get_status(self) -> DetectorStatus:
        with self.status_lock:
            return self.status.model_copy()

    def update_frame(self, new_frame: np.ndarray) -> None:
        with self.frame_lock:
            self.frame = new_frame.copy()

    def get_frame(self) -> Optional[np.ndarray]:
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None
