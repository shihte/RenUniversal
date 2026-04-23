"""
校準精靈技能邏輯 (Calibration Wizard Skill Logic)
引導使用者完成基準姿勢的採樣與計算。
"""

import time
import numpy as np
from typing import List, Optional
from .schema import CalibrationResult

class CalibrationWizardSkill:
    """
    引導使用者進行姿勢校準的精靈。
    
    該技能會在指定時間內收集面部距離樣本，並計算其平均值作為後續檢測的基準。
    遵循 Pattern: Inversion。
    """
    
    def __init__(self, duration: float = 3.0):
        """
        初始化校準精靈。
        
        Args:
            duration (float): 校準所需的持續時間（秒）。
        """
        self.duration = duration
        self.start_time: Optional[float] = None
        self.samples_eye_distance: List[float] = []
        self.samples_nose_chin_distance: List[float] = []
        self.is_complete = False

    def reset(self) -> None:
        """重置精靈狀態，準備重新執行校準。"""
        self.start_time = None
        self.samples_eye_distance = []
        self.samples_nose_chin_distance = []
        self.is_complete = False

    def process(self, current_eye_distance: float, current_nose_chin_distance: float) -> CalibrationResult:
        """
        處理當前的採樣數據並更新校準進度。
        
        Args:
            current_eye_distance (float): 當前幀的眼距。
            current_nose_chin_distance (float): 當前幀的鼻尖至下巴距離。
            
        Returns:
            CalibrationResult: 包含進度、結果與導引訊息的狀態物件。
        """
        # 若已完成，直接返回最終結果
        if self.is_complete:
            return CalibrationResult(
                is_complete=True, 
                progress=100,
                baseline_eye_dist=float(np.mean(self.samples_eye_distance)),
                baseline_nc_dist=float(np.mean(self.samples_nose_chin_distance)),
                message="Calibration complete"
            )

        # 首次啟動計時
        if self.start_time is None:
            self.start_time = time.time()
        
        elapsed_time = time.time() - self.start_time
        progress_percentage = min(int((elapsed_time / self.duration) * 100), 100)
        
        # 收集樣本
        self.samples_eye_distance.append(current_eye_distance)
        self.samples_nose_chin_distance.append(current_nose_chin_distance)
        
        # 檢查是否達到結束時間
        if elapsed_time >= self.duration:
            self.is_complete = True
            return CalibrationResult(
                is_complete=True, 
                progress=100,
                baseline_eye_dist=float(np.mean(self.samples_eye_distance)),
                baseline_nc_dist=float(np.mean(self.samples_nose_chin_distance)),
                message="Calibration finished successfully"
            )
        
        return CalibrationResult(
            is_complete=False, 
            progress=progress_percentage,
            message="Please look straight ahead and hold steady..."
        )
