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
        
        if not rules:
            return False, 0.0, {"error": "No rules defined in skill config"}

        # Evaluate defined rules (Custom Syntax parsing)
        import re
        
        POINT_ALIASES = {
            "nose": self.NOSE_INDEX,
            "chin": self.CHIN_INDEX,
            "left_eye": self.LEFT_EYE_INDEX,
            "right_eye": self.RIGHT_EYE_INDEX,
            "left_shoulder": 11,
            "right_shoulder": 12,
        }

        # If rules is an array of strings, use the first one (from UI syntax input)
        if isinstance(rules, list) and len(rules) > 0 and isinstance(rules[0], str):
            syntax_str = rules[0]
            
            # Parsing: e.g. "nose,chin >< 20%" or "left_shoulder,right_shoulder >><< num=15" or "33,263 >< 20%"
            match = re.match(r"([a-zA-Z0-9_]+),([a-zA-Z0-9_]+)\s*(><|<>|>><<)\s*(?:num=)?([0-9.]+)%?", syntax_str.strip())
            
            if match:
                pt1_name, pt2_name, direction, num_str = match.groups()
                threshold_percent = float(num_str) / 100.0
                
                def get_point_coordinates(pt_str, landmarks_obj, is_baseline=False, dim=(1,1)):
                    idx = -1
                    if pt_str.isdigit():
                        idx = int(pt_str)
                    elif pt_str in POINT_ALIASES:
                        idx = POINT_ALIASES[pt_str]
                        
                    if idx != -1 and landmarks_obj is not None:
                        try:
                            if is_baseline:
                                # baselines are list of dicts {"x": float, "y": float}
                                if idx < len(landmarks_obj):
                                    pt = landmarks_obj[idx]
                                    return pt["x"] * dim[0], pt["y"] * dim[1]
                            else:
                                # raw mediapipe normalized landmarks
                                if idx < len(landmarks_obj.landmark):
                                    pt = landmarks_obj.landmark[idx]
                                    return pt.x * dim[0], pt.y * dim[1]
                        except Exception:
                            pass
                    return None

                # Attempt to calculate current and baseline distance
                current_dist = -1.0
                baseline_dist = -1.0
                
                # Check if it's a predefined pair with existing logic first
                pair = {pt1_name, pt2_name}
                if pair == {"nose", "chin"}:
                    current_dist = math.sqrt(((features.get("nose_x", 0) - features.get("chin_x", 0))**2) + ((features.get("nose_y", 0) - features.get("chin_y", 0))**2)) if "nose_x" in features else -1.0
                    # Fallback to direct calculation
                    if current_dist <= 0 and face_landmarks:
                        n = face_landmarks.landmark[self.NOSE_INDEX]
                        c = face_landmarks.landmark[self.CHIN_INDEX]
                        current_dist = math.sqrt(((n.x-c.x)*face_dim[0])**2 + ((n.y-c.y)*face_dim[1])**2)
                    baseline_dist = baselines.get("nose_chin_distance", -1)
                
                elif pair == {"left_eye", "right_eye"}:
                    if face_landmarks:
                        l = face_landmarks.landmark[self.LEFT_EYE_INDEX]
                        r = face_landmarks.landmark[self.RIGHT_EYE_INDEX]
                        current_dist = abs((r.x - l.x) * face_dim[0])
                    baseline_dist = baselines.get("eye_distance", -1)
                    
                elif pair == {"left_shoulder", "right_shoulder"}:
                    if pose_landmarks:
                        l = pose_landmarks.landmark[11]
                        r = pose_landmarks.landmark[12]
                        current_dist = math.sqrt(((l.x-r.x)*body_dim[0])**2 + ((l.y-r.y)*body_dim[1])**2)
                    baseline_dist = baselines.get("shoulder_width", -1)
                    
                else:
                    # Generic point calculation using full landmark arrays
                    target_landmarks = pose_landmarks if (pt1_name in ["left_shoulder", "right_shoulder"] or pt2_name in ["left_shoulder", "right_shoulder"]) else face_landmarks
                    target_dim = body_dim if target_landmarks == pose_landmarks else face_dim
                    target_baselines = baselines.get("pose_landmarks") if target_landmarks == pose_landmarks else baselines.get("face_landmarks")

                    p1_curr = get_point_coordinates(pt1_name, target_landmarks, is_baseline=False, dim=target_dim)
                    p2_curr = get_point_coordinates(pt2_name, target_landmarks, is_baseline=False, dim=target_dim)
                    p1_base = get_point_coordinates(pt1_name, target_baselines, is_baseline=True, dim=target_dim)
                    p2_base = get_point_coordinates(pt2_name, target_baselines, is_baseline=True, dim=target_dim)

                    if p1_curr and p2_curr:
                        current_dist = math.sqrt((p1_curr[0]-p2_curr[0])**2 + (p1_curr[1]-p2_curr[1])**2)
                    if p1_base and p2_base:
                        baseline_dist = math.sqrt((p1_base[0]-p2_base[0])**2 + (p1_base[1]-p2_base[1])**2)

                if current_dist > 0 and baseline_dist > 0:
                    ratio = (current_dist - baseline_dist) / baseline_dist
                    primary_val = ratio
                    
                    if pair == {"nose", "chin"}:
                        # Apply low-head yaw tolerance filtering & hysteresis
                        yaw_tol = preferences.get("yaw_tolerance", 0.10)
                        is_turning = features.get("yaw_deviation", 0.0) > yaw_tol
                        info["is_turning"] = is_turning
                        if is_turning:
                            is_bad = False
                        else:
                            is_bad_previously = state_history.get("is_bad_posture", False)
                            if is_bad_previously:
                                is_bad = ratio <= -threshold_percent + 0.05
                            else:
                                is_bad = ratio < -threshold_percent
                    else:
                        if direction == "><":
                            is_bad = ratio <= -threshold_percent
                        elif direction == "<>":
                            is_bad = ratio >= threshold_percent
                        elif direction == ">><<":
                            is_bad = abs(ratio) >= threshold_percent
                    
                    info["custom_ratio"] = float(round(ratio * 100, 1))
                    return is_bad, primary_val, info
                else:
                    info["error"] = f"Points {pt1_name},{pt2_name} not detected or baselines missing"
                    return False, 0.0, info
            else:
                info["error"] = "Invalid rule syntax"
                return False, 0.0, info

        # If rules are provided in the old dict format
        rule_results = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
                
            feat_name = rule.get("feature")
            val = features.get(feat_name, 0.0)
            primary_val = val
            
            op = rule.get("operator")
            thresh_key = rule.get("threshold_key", "threshold")
            default_thresh = self.config.get("default_preferences", {}).get(thresh_key, 0.10)
            threshold = preferences.get(thresh_key, default_thresh)
            
            # Comparison
            res = False
            if feat_name == "nose_chin_ratio":
                # Special handling for slouch to match negation & yaw & hysteresis
                yaw_tol = preferences.get("yaw_tolerance", 0.10)
                is_turning = features.get("yaw_deviation", 0.0) > yaw_tol
                info["is_turning"] = is_turning
                if is_turning:
                    res = False
                else:
                    is_bad_previously = state_history.get("is_bad_posture", False)
                    if is_bad_previously:
                        res = val <= -threshold + 0.05
                    else:
                        res = val < -threshold
            else:
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
                    
            rule_results.append(res)
            
        is_bad = all(rule_results) if rule_results else False
        return is_bad, primary_val, info
