"""
姿勢審查技能邏輯 (Posture Reviewer Skill Logic)
負責根據 Mediapipe Landmarks 評估使用者的坐姿健康狀況。
"""

import math
from typing import Any, Tuple, Optional
from .schema import PostureReport, PostureMetrics

class PostureReviewerSkill:
    """
    負責審核姿勢數據是否符合健康規範。
    
    該技能專注於幾何關係的推理，判斷點位間的比率是否超出預設閾值。
    遵循 Pattern: Reviewer。
    """
    
    def __init__(self, threshold_ratio: float = 0.20, yaw_tolerance: float = 0.10):
        """
        初始化審查技能。
        
        Args:
            threshold_ratio (float): 低頭比例後的觸發閾值（預設 20%）。
            yaw_tolerance (float): 左右轉頭的過濾容差（預設 10%）。
        """
        self.threshold_ratio = threshold_ratio
        self.yaw_tolerance = yaw_tolerance
        
        # Mediapipe 面部地標索引 (Landmark Indices)
        self.NOSE_INDEX = 1
        self.CHIN_INDEX = 152
        self.LEFT_EYE_INDEX = 33
        self.RIGHT_EYE_INDEX = 263

    def _calculate_euclidean_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """計算兩點間的歐幾里得距離。"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    def evaluate(self, 
                 landmarks: Any, 
                 width: int, 
                 height: int, 
                 baseline_eye_distance: float, 
                 baseline_nose_chin_distance: float,
                 is_down_previously: bool) -> PostureReport:
        """
        根據基準值審查當前姿勢。
        
        Args:
            landmarks (Any): Mediapipe 偵測到的面部地標。
            width (int): 影像寬度。
            height (int): 影像高度。
            baseline_eye_distance (float): 校準後的基準眼距。
            baseline_nose_chin_distance (float): 校準後的基準鼻尖到下巴距離。
            is_down_previously (bool): 前一幀是否處於不良姿勢狀態（用於磁滯效應）。
            
        Returns:
            PostureReport: 包含詳細指標與判斷結果的審查報告。
        """
        if not landmarks:
            return PostureReport(is_valid=False, timestamp=0.0, error_message="No landmarks detected")

        # 1. 座標解析與像素轉換
        nose = landmarks.landmark[self.NOSE_INDEX]
        chin = landmarks.landmark[self.CHIN_INDEX]
        left_eye = landmarks.landmark[self.LEFT_EYE_INDEX]
        right_eye = landmarks.landmark[self.RIGHT_EYE_INDEX]

        nose_point = (nose.x * width, nose.y * height)
        chin_point = (chin.x * width, chin.y * height)
        left_eye_point = (left_eye.x * width, left_eye.y * height)
        right_eye_point = (right_eye.x * width, right_eye.y * height)

        # 2. 幾何指標計算
        current_eye_distance = abs(right_eye_point[0] - left_eye_point[0])
        current_nose_chin_distance = self._calculate_euclidean_distance(nose_point, chin_point)

        # 3. 轉頭過濾 (Yaw Filtering)
        # 用於判斷使用者是否正在側頭，避免誤報。
        yaw_deviation = abs(current_eye_distance - baseline_eye_distance) / baseline_eye_distance if baseline_eye_distance else 0
        is_turning = yaw_deviation > self.yaw_tolerance

        # 4. 比例計算與低頭判斷
        # nc_ratio 為負值代表距離縮短，即低頭。
        nc_ratio = (current_nose_chin_distance - baseline_nose_chin_distance) / baseline_nose_chin_distance if baseline_nose_chin_distance else 0
        
        is_bad_posture = False
        if not is_turning:
            # 引入磁滯效應 (Hysteresis) 避免在閾值邊緣抖動
            if is_down_previously:
                # 若先前已顯示不良姿勢，則需要恢復更多（+5%）才算正常
                is_bad_posture = nc_ratio <= -self.threshold_ratio + 0.05
            else:
                # 初始觸發閾值
                is_bad_posture = nc_ratio < -self.threshold_ratio

        return PostureReport(
            is_valid=True,
            timestamp=0.0,
            metrics=PostureMetrics(
                eye_dist=current_eye_distance,
                nose_chin_dist=current_nose_chin_distance,
                nc_ratio=nc_ratio,
                is_turning=is_turning,
                is_bad_posture=is_bad_posture
            )
        )
