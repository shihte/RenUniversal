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
        self.samples_shoulder_width: List[float] = []
        self.samples_shoulder_midpoint_x: List[float] = []
        self.samples_shoulder_midpoint_y: List[float] = []
        self.is_complete = False

    def reset(self) -> None:
        """重置精靈狀態，準備重新執行校準。"""
        self.start_time = None
        self.samples_eye_distance = []
        self.samples_nose_chin_distance = []
        self.samples_shoulder_width = []
        self.samples_shoulder_midpoint_x = []
        self.samples_shoulder_midpoint_y = []
        self.last_face_landmarks = None
        self.last_pose_landmarks = None
        self.is_complete = False

    def process(self, 
                current_eye_distance: float, 
                current_nose_chin_distance: float,
                current_shoulder_width: float = 0.0,
                current_shoulder_midpoint_x: float = 0.0,
                current_shoulder_midpoint_y: float = 0.0,
                face_landmarks: Optional[List[dict]] = None,
                pose_landmarks: Optional[List[dict]] = None) -> CalibrationResult:
        """
        處理當前的採樣數據並更新校準進度。
        
        Args:
            current_eye_distance (float): 當前幀的眼距。
            current_nose_chin_distance (float): 當前幀的鼻尖至下巴距離。
            current_shoulder_width (float): 當前幀的肩膀寬度。
            current_shoulder_midpoint_x (float): 當前幀的肩膀中點 X。
            current_shoulder_midpoint_y (float): 當前幀的肩膀中點 Y。
            
        Returns:
            CalibrationResult: 包含進度、結果與導引訊息的狀態物件。
        """
        # 若已完成，直接返回最終結果
        if self.is_complete:
            return CalibrationResult(
                is_complete=True, 
                progress=100,
                baseline_eye_dist=float(np.mean(self.samples_eye_distance)) if self.samples_eye_distance else 0.0,
                baseline_nc_dist=float(np.mean(self.samples_nose_chin_distance)) if self.samples_nose_chin_distance else 0.0,
                baseline_shoulder_width=float(np.mean(self.samples_shoulder_width)) if self.samples_shoulder_width else 0.0,
                baseline_shoulder_midpoint_x=float(np.mean(self.samples_shoulder_midpoint_x)) if self.samples_shoulder_midpoint_x else 0.0,
                baseline_shoulder_midpoint_y=float(np.mean(self.samples_shoulder_midpoint_y)) if self.samples_shoulder_midpoint_y else 0.0,
                baseline_face_landmarks=self.last_face_landmarks,
                baseline_pose_landmarks=self.last_pose_landmarks,
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
        if current_shoulder_width > 0:
            self.samples_shoulder_width.append(current_shoulder_width)
            self.samples_shoulder_midpoint_x.append(current_shoulder_midpoint_x)
            self.samples_shoulder_midpoint_y.append(current_shoulder_midpoint_y)
            
        if face_landmarks:
            self.last_face_landmarks = face_landmarks
        if pose_landmarks:
            self.last_pose_landmarks = pose_landmarks
        
        # 檢查是否達到結束時間
        if elapsed_time >= self.duration:
            self.is_complete = True
            return CalibrationResult(
                is_complete=True, 
                progress=100,
                baseline_eye_dist=float(np.mean(self.samples_eye_distance)) if self.samples_eye_distance else 0.0,
                baseline_nc_dist=float(np.mean(self.samples_nose_chin_distance)) if self.samples_nose_chin_distance else 0.0,
                baseline_shoulder_width=float(np.mean(self.samples_shoulder_width)) if self.samples_shoulder_width else 0.0,
                baseline_shoulder_midpoint_x=float(np.mean(self.samples_shoulder_midpoint_x)) if self.samples_shoulder_midpoint_x else 0.0,
                baseline_shoulder_midpoint_y=float(np.mean(self.samples_shoulder_midpoint_y)) if self.samples_shoulder_midpoint_y else 0.0,
                baseline_face_landmarks=self.last_face_landmarks,
                baseline_pose_landmarks=self.last_pose_landmarks,
                message="Calibration finished successfully"
            )
        
        return CalibrationResult(
            is_complete=False, 
            progress=progress_percentage,
            message="Please look straight ahead and hold steady..."
        )
