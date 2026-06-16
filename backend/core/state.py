import threading
import numpy as np
import json
import os
import time
from typing import Optional, Dict, Any, Tuple
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
        
        # 網路手機攝影機資料
        self.network_frame: Optional[np.ndarray] = None
        self.last_network_frame_time: float = 0.0
        self.network_frame_lock = threading.Lock()
        
        # 個人化偏好 (Memory)
        self.prefs = self._load_prefs()

        # Posture 狀態
        self.status = DetectorStatus(
            threshold=float(self.prefs.get("threshold_ratio", 0.20) * 100),
            yaw_tolerance=float(self.prefs.get("yaw_tolerance", 0.10) * 100),
            sway_threshold=float(self.prefs.get("sway_threshold", 0.15) * 100),
            lean_threshold=float(self.prefs.get("lean_threshold", 0.10) * 100),
            camera_source=["local_0"], # ALWAYS default to local_0 regardless of preferences
            flip_enabled=self.prefs.get("flip_enabled", True),
            privacy_mode=self.prefs.get("privacy_mode", True)
        )
        self.status_lock = threading.Lock()
        
        logger.info(f"SharedState initialized. Memory loaded from {prefs_path}")

    def _load_prefs(self) -> Dict[str, Any]:
        """從本地檔案載入使用者偏好。"""
        default_prefs = {
            "threshold_ratio": 0.20,
            "yaw_tolerance": 0.10,
            "sway_threshold": 0.15,
            "lean_threshold": 0.10,
            "username": "User",
            "last_baseline_eye": 0.0,
            "camera_source": "local_0",
            "flip_enabled": True,
            "privacy_mode": True
        }
        if self.prefs_path.exists():
            try:
                with open(self.prefs_path, "r") as f:
                    return {**default_prefs, **json.load(f)}
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
        return default_prefs

    def save_prefs(self, new_prefs: Dict[str, Any]) -> None:
        """持久化儲存使用者偏好並同步更新檢測狀態。"""
        self.prefs.update(new_prefs)
        
        with self.status_lock:
            current_dict = self.status.model_dump()
            
            # 數值單位雙向轉換與映射
            if "threshold" in new_prefs:
                current_dict["threshold"] = float(new_prefs["threshold"])
                self.prefs["threshold_ratio"] = float(new_prefs["threshold"]) / 100.0
            elif "threshold_ratio" in new_prefs:
                current_dict["threshold"] = float(new_prefs["threshold_ratio"]) * 100.0
                
            if "yaw_tolerance" in new_prefs:
                val = float(new_prefs["yaw_tolerance"])
                if val <= 1.0:
                    current_dict["yaw_tolerance"] = val * 100.0
                    self.prefs["yaw_tolerance"] = val
                else:
                    current_dict["yaw_tolerance"] = val
                    self.prefs["yaw_tolerance"] = val / 100.0
                    
            if "sway_threshold" in new_prefs:
                val = float(new_prefs["sway_threshold"])
                if val <= 1.0:
                    current_dict["sway_threshold"] = val * 100.0
                    self.prefs["sway_threshold"] = val
                else:
                    current_dict["sway_threshold"] = val
                    self.prefs["sway_threshold"] = val / 100.0
                    
            if "lean_threshold" in new_prefs:
                val = float(new_prefs["lean_threshold"])
                if val <= 1.0:
                    current_dict["lean_threshold"] = val * 100.0
                    self.prefs["lean_threshold"] = val
                else:
                    current_dict["lean_threshold"] = val
                    self.prefs["lean_threshold"] = val / 100.0
                    
            if "camera_source" in new_prefs:
                src = new_prefs["camera_source"]
                if isinstance(src, list):
                    current_dict["camera_source"] = [str(x) for x in src]
                else:
                    current_dict["camera_source"] = str(src)
                
            if "flip_enabled" in new_prefs:
                current_dict["flip_enabled"] = bool(new_prefs["flip_enabled"])
                
            if "privacy_mode" in new_prefs:
                current_dict["privacy_mode"] = bool(new_prefs["privacy_mode"])
                
            self.status = DetectorStatus(**current_dict)
            
        try:
            with open(self.prefs_path, "w") as f:
                persistent_prefs = {
                    k: v for k, v in self.prefs.items()
                    if not ("threshold" in k or "tolerance" in k)
                }
                json.dump(persistent_prefs, f, indent=4)
            logger.info("Preferences saved (sliders excluded for memory-only tuning)")
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

    def update_network_frame(self, frame: np.ndarray) -> None:
        with self.network_frame_lock:
            self.network_frame = frame.copy()
            self.last_network_frame_time = time.time()

    def get_network_frame(self) -> Tuple[Optional[np.ndarray], float]:
        with self.network_frame_lock:
            if self.network_frame is not None:
                return self.network_frame.copy(), self.last_network_frame_time
            return None, 0.0
