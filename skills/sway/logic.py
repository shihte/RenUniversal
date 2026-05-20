import math
from typing import Dict, Any, Tuple

class ActionDetector:
    """
    左右搖晃與側傾偵測器。
    計算肩膀中點相對於校準基準的水平偏移量與兩肩膀高度差比例。
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.LEFT_EYE_INDEX = 33
        self.RIGHT_EYE_INDEX = 263

    def evaluate(self, 
                 face_landmarks: Any, 
                 pose_landmarks: Any, 
                 face_dim: Tuple[int, int],
                 body_dim: Tuple[int, int],
                 baselines: Dict[str, float], 
                 preferences: Dict[str, Any],
                 state_history: Dict[str, Any]) -> Tuple[bool, float, Dict[str, Any]]:
        
        baseline_shoulder_width = baselines.get("shoulder_width", 0.0)
        baseline_shoulder_midpoint_x = baselines.get("shoulder_midpoint_x", 0.0)
        
        if baseline_shoulder_width <= 0:
            return False, 0.0, {"reason": "No baseline shoulder width calibrated"}

        sway_threshold = preferences.get("sway_threshold", self.config["default_preferences"]["sway_threshold"])
        
        displacement_ratio = 0.0
        tilt_ratio = 0.0

        if pose_landmarks:
            # 使用 Body (手機/後置) 鏡頭維度
            b_width, b_height = body_dim
            left_shoulder = pose_landmarks.landmark[11]
            right_shoulder = pose_landmarks.landmark[12]
            
            ls_point = (left_shoulder.x * b_width, left_shoulder.y * b_height)
            rs_point = (right_shoulder.x * b_width, right_shoulder.y * b_height)
            
            current_shoulder_width = math.sqrt(
                (ls_point[0] - rs_point[0])**2 + (ls_point[1] - rs_point[1])**2
            )
            current_shoulder_midpoint_x = (ls_point[0] + rs_point[0]) / 2.0
            
            # 肩膀傾斜度 (y軸高度差 / 肩寬)
            tilt_ratio = abs(rs_point[1] - ls_point[1]) / current_shoulder_width if current_shoulder_width else 0.0
            # 肩膀水平偏移比
            displacement_ratio = (current_shoulder_midpoint_x - baseline_shoulder_midpoint_x) / baseline_shoulder_width
        else:
            # 備用方案：使用 Face Mesh (電腦/前置) 鏡頭維度
            if not face_landmarks:
                return False, 0.0, {"reason": "No landmarks detected"}
            
            f_width, f_height = face_dim
            left_eye_l = face_landmarks.landmark[self.LEFT_EYE_INDEX]
            right_eye_l = face_landmarks.landmark[self.RIGHT_EYE_INDEX]
            left_eye_p = (left_eye_l.x * f_width, left_eye_l.y * f_height)
            right_eye_p = (right_eye_l.x * f_width, right_eye_l.y * f_height)
            
            current_eye_dist = abs(right_eye_p[0] - left_eye_p[0])
            face_center_x = (left_eye_p[0] + right_eye_p[0]) / 2.0
            
            # 以臉部傾斜取代
            tilt_ratio = abs(right_eye_p[1] - left_eye_p[1]) / current_eye_dist if current_eye_dist else 0.0
            displacement_ratio = (face_center_x - baseline_shoulder_midpoint_x) / baseline_shoulder_width

        # 綜合搖晃比
        sway_ratio = max(abs(displacement_ratio), tilt_ratio)
        is_swaying = sway_ratio > sway_threshold

        return is_swaying, sway_ratio, {
            "displacement_ratio": float(round(displacement_ratio, 3)),
            "tilt_ratio": float(round(tilt_ratio, 3)),
            "sway_ratio": float(round(sway_ratio, 3))
        }
