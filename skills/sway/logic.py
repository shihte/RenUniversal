import math
from typing import Tuple, Dict, Any

class ActionDetector:
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
        
        features = {}
        info = {}
        
        # Extract Face Mesh Features
        if face_landmarks:
            width, height = face_dim
            nose = face_landmarks.landmark[self.NOSE_INDEX]
            chin = face_landmarks.landmark[self.CHIN_INDEX]
            left_eye = face_landmarks.landmark[self.LEFT_EYE_INDEX]
            right_eye = face_landmarks.landmark[self.RIGHT_EYE_INDEX]
            
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
            
            yaw_deviation = 0.0
            if baseline_eye_distance > 0:
                yaw_deviation = abs(current_eye_distance - baseline_eye_distance) / baseline_eye_distance
                
            nc_ratio = 0.0
            if baseline_nose_chin_distance > 0:
                nc_ratio = (current_nose_chin_distance - baseline_nose_chin_distance) / baseline_nose_chin_distance
                
            features["yaw_deviation"] = yaw_deviation
            features["nose_chin_ratio"] = nc_ratio
            
            info["yaw_deviation"] = float(round(yaw_deviation, 3))
            info["nc_ratio_percent"] = float(round(nc_ratio * 100, 1))

        # Extract Pose Features
        if pose_landmarks:
            width, height = body_dim
            left_shoulder = pose_landmarks.landmark[11]
            right_shoulder = pose_landmarks.landmark[12]
            
            sh_l = (left_shoulder.x * width, left_shoulder.y * height)
            sh_r = (right_shoulder.x * width, right_shoulder.y * height)
            
            sh_width = math.sqrt((sh_l[0] - sh_r[0])**2 + (sh_l[1] - sh_r[1])**2)
            sh_mid_x = (sh_l[0] + sh_r[0]) / 2.0
            sh_mid_y = (sh_l[1] + sh_r[1]) / 2.0
            
            baseline_shoulder_width = baselines.get("shoulder_width", 0.0)
            baseline_shoulder_midpoint_x = baselines.get("shoulder_midpoint_x", 0.0)
            baseline_shoulder_midpoint_y = baselines.get("shoulder_midpoint_y", 0.0)
            
            sway_ratio = 0.0
            lean_ratio = 0.0
            if baseline_shoulder_width > 0:
                sway_ratio = abs(sh_mid_x - baseline_shoulder_midpoint_x) / baseline_shoulder_width
                lean_ratio = (sh_mid_y - baseline_shoulder_midpoint_y) / baseline_shoulder_width
                
            shoulder_slope = abs(sh_l[1] - sh_r[1]) / (sh_width if sh_width > 0 else 1.0)
            
            features["torso_sway"] = sway_ratio
            features["torso_lean"] = lean_ratio
            features["shoulder_slope"] = shoulder_slope
            
            info["torso_sway"] = float(round(sway_ratio, 3))
            info["torso_lean"] = float(round(lean_ratio, 3))
            info["shoulder_slope"] = float(round(shoulder_slope, 3))

        # Evaluate rules defined in config
        rules = self.config.get("rules", [])
        is_bad = False
        primary_val = 0.0
        
        # Default behavior if no rules (fallback to name-based evaluation)
        if not rules:
            name = self.config.get("name", "")
            if name == "slouch":
                threshold = preferences.get("threshold_ratio", 0.20)
                yaw_tol = preferences.get("yaw_tolerance", 0.10)
                is_turning = features.get("yaw_deviation", 0.0) > yaw_tol
                info["is_turning"] = is_turning
                val = features.get("nose_chin_ratio", 0.0)
                primary_val = val
                if not is_turning:
                    is_bad_previously = state_history.get("is_bad_posture", False)
                    if is_bad_previously:
                        is_bad = val <= -threshold + 0.05
                    else:
                        is_bad = val < -threshold
            elif name == "sway":
                threshold = preferences.get("sway_threshold", 0.15)
                val = features.get("torso_sway", 0.0)
                primary_val = val
                is_bad = val > threshold
            elif name == "lean":
                threshold = preferences.get("lean_threshold", 0.10)
                val = features.get("torso_lean", 0.0)
                primary_val = val
                is_bad = val > threshold
            return is_bad, primary_val, info

        # Evaluate defined rules
        rule_results = []
        for rule in rules:
            feat_name = rule.get("feature")
            val = features.get(feat_name, 0.0)
            primary_val = val
            
            op = rule.get("operator")
            thresh_key = rule.get("threshold_key", "threshold")
            default_thresh = self.config.get("default_preferences", {}).get(thresh_key, 0.10)
            threshold = preferences.get(thresh_key, default_thresh)
            
            # Comparison
            res = False
            if op == ">":
                res = val > threshold
            elif op == "<":
                res = val < threshold
            elif op == ">=":
                res = val >= threshold
            elif op == "<=":
                res = val <= threshold
            elif op == "==":
                res = abs(val - threshold) < 1e-5
            
            if feat_name == "nose_chin_ratio":
                yaw_tol = preferences.get("yaw_tolerance", 0.10)
                is_turning = features.get("yaw_deviation", 0.0) > yaw_tol
                info["is_turning"] = is_turning
                if is_turning:
                    res = False
                    
            rule_results.append(res)
            
        is_bad = all(rule_results) if rule_results else False
        
        return is_bad, primary_val, info
