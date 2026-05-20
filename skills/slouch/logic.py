import math
from typing import Dict, Any, Tuple

class ActionDetector:
    """
    駝背與低頭偵測器。
    計算鼻尖到下巴之投影距離，並利用眼距（Yaw 轉頭）進行雜訊過濾。
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.NOSE_INDEX = 1
        self.CHIN_INDEX = 152
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
        
        if not face_landmarks:
            return False, 0.0, {"reason": "No face mesh detected"}

        width, height = face_dim
        nose = face_landmarks.landmark[self.NOSE_INDEX]
        chin = face_landmarks.landmark[self.CHIN_INDEX]
        left_eye = face_landmarks.landmark[self.LEFT_EYE_INDEX]
        right_eye = face_landmarks.landmark[self.RIGHT_EYE_INDEX]

        # 轉換為像素座標
        nose_point = (nose.x * width, nose.y * height)
        chin_point = (chin.x * width, chin.y * height)
        left_eye_point = (left_eye.x * width, left_eye.y * height)
        right_eye_point = (right_eye.x * width, right_eye.y * height)

        current_eye_distance = abs(right_eye_point[0] - left_eye_point[0])
        current_nose_chin_distance = math.sqrt(
            (nose_point[0] - chin_point[0])**2 + (nose_point[1] - chin_point[1])**2
        )

        baseline_eye_distance = baselines.get("eye_distance", 0.0)
        baseline_nose_chin_distance = baselines.get("nose_chin_distance", 0.0)

        # 1. 轉頭過濾 (Yaw Filtering)
        yaw_deviation = 0.0
        if baseline_eye_distance > 0:
            yaw_deviation = abs(current_eye_distance - baseline_eye_distance) / baseline_eye_distance
        
        # 優先讀取 runtime preferences，否則使用預設值
        yaw_tolerance = preferences.get("yaw_tolerance", self.config["default_preferences"]["yaw_tolerance"])
        is_turning = yaw_deviation > yaw_tolerance

        # 2. 駝背比例計算
        nc_ratio = 0.0
        if baseline_nose_chin_distance > 0:
            nc_ratio = (current_nose_chin_distance - baseline_nose_chin_distance) / baseline_nose_chin_distance

        threshold_ratio = preferences.get("threshold_ratio", self.config["default_preferences"]["threshold_ratio"])

        is_bad = False
        if not is_turning:
            # 引入遲滯區 (Hysteresis) 避免警報邊緣閃爍
            is_bad_previously = state_history.get("is_bad_posture", False)
            if is_bad_previously:
                # 若先前已判定駝背，需回升到高於閥值 5% 才能解除
                is_bad = nc_ratio <= -threshold_ratio + 0.05
            else:
                is_bad = nc_ratio < -threshold_ratio

        return is_bad, nc_ratio, {
            "is_turning": is_turning,
            "yaw_deviation": float(round(yaw_deviation, 3)),
            "nc_ratio_percent": float(round(nc_ratio * 100, 1)),
            "current_nc_dist": float(round(current_nose_chin_distance, 1))
        }
