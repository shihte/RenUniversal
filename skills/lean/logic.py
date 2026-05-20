import math
from typing import Dict, Any, Tuple

class ActionDetector:
    """
    身體前傾偵測器。
    基於肩膀寬度在二維投影中的變寬 (lean_width_ratio) 或中點垂直下沉 (lean_y_ratio)。
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
        baseline_shoulder_midpoint_y = baselines.get("shoulder_midpoint_y", 0.0)
        baseline_eye_distance = baselines.get("eye_distance", 0.0)

        if baseline_shoulder_width <= 0:
            return False, 0.0, {"reason": "No baseline shoulder width calibrated"}

        lean_threshold = preferences.get("lean_threshold", self.config["default_preferences"]["lean_threshold"])

        lean_width_ratio = 0.0
        lean_y_ratio = 0.0

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
            current_shoulder_midpoint_y = (ls_point[1] + rs_point[1]) / 2.0
            
            # 肩膀投影寬度增加比例 (前傾時會顯得比較寬)
            lean_width_ratio = (current_shoulder_width - baseline_shoulder_width) / baseline_shoulder_width
            # 肩膀中點下沉比例
            lean_y_ratio = (current_shoulder_midpoint_y - baseline_shoulder_midpoint_y) / baseline_shoulder_width
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
            face_center_y = (left_eye_p[1] + right_eye_p[1]) / 2.0
            
            if baseline_eye_distance > 0:
                ratio = baseline_shoulder_width / baseline_eye_distance
                current_shoulder_width = current_eye_dist * ratio
            else:
                current_shoulder_width = current_eye_dist * 4.5
            
            current_shoulder_midpoint_y = face_center_y + current_eye_dist * 3.0
            
            lean_width_ratio = (current_shoulder_width - baseline_shoulder_width) / baseline_shoulder_width
            lean_y_ratio = (current_shoulder_midpoint_y - baseline_shoulder_midpoint_y) / baseline_shoulder_width

        # 綜合前傾度
        lean_ratio = max(lean_width_ratio, lean_y_ratio)
        is_leaning = lean_ratio > lean_threshold

        return is_leaning, lean_ratio, {
            "lean_width_ratio": float(round(lean_width_ratio, 3)),
            "lean_y_ratio": float(round(lean_y_ratio, 3)),
            "lean_ratio": float(round(lean_ratio, 3))
        }
