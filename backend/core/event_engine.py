import os
import json
import logging
import re
import math

class EventEngine:
    def __init__(self, events_dir):
        self.events_dir = events_dir
        self.events = {}
        self.logger = logging.getLogger("EventEngine")
        self.load_all_events()

    def load_all_events(self):
        self.events = {}
        if not os.path.exists(self.events_dir):
            os.makedirs(self.events_dir, exist_ok=True)
            return

        for folder in os.listdir(self.events_dir):
            folder_path = os.path.join(self.events_dir, folder)
            if not os.path.isdir(folder_path):
                continue
                
            config_path = os.path.join(folder_path, 'config.json')
            if not os.path.exists(config_path):
                continue
                
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                if not config.get('enabled', True):
                    continue
                    
                self.events[folder] = config
                self.logger.info(f"Loaded event rule: {folder}")
            except Exception as e:
                self.logger.error(f"Failed to load event {folder}: {e}")

    def reload(self):
        self.load_all_events()

    def get_landmark_coords(self, pt_id, landmarks, pose_landmarks, face_dim, body_dim):
        pt_id = str(pt_id).strip()
        is_pose = False
        idx_str = pt_id
        if pt_id.startswith('p'):
            is_pose = True
            idx_str = pt_id[1:]
        elif pt_id.startswith('f'):
            is_pose = False
            idx_str = pt_id[1:]
        else:
            try:
                val = int(pt_id)
                if val <= 32:
                    is_pose = (pose_landmarks is not None)
                else:
                    is_pose = False
            except ValueError:
                return None
        
        try:
            idx = int(idx_str)
        except ValueError:
            return None
            
        if is_pose:
            if not pose_landmarks:
                return None
            w, h = body_dim
            if isinstance(pose_landmarks, list):
                if idx < len(pose_landmarks):
                    pt = pose_landmarks[idx]
                    if hasattr(pt, 'x') and hasattr(pt, 'y'):
                        return pt.x * w, pt.y * h
                    elif isinstance(pt, dict):
                        return pt.get("x", 0.0) * w, pt.get("y", 0.0) * h
            else:
                if hasattr(pose_landmarks, 'landmark') and idx < len(pose_landmarks.landmark):
                    pt = pose_landmarks.landmark[idx]
                    return pt.x * w, pt.y * h
        else:
            if not landmarks:
                return None
            w, h = face_dim
            if isinstance(landmarks, list):
                if idx < len(landmarks):
                    pt = landmarks[idx]
                    if hasattr(pt, 'x') and hasattr(pt, 'y'):
                        return pt.x * w, pt.y * h
                    elif isinstance(pt, dict):
                        return pt.get("x", 0.0) * w, pt.get("y", 0.0) * h
            else:
                lms = landmarks
                if hasattr(landmarks, 'landmark'):
                    lms = landmarks.landmark
                elif hasattr(landmarks, 'multi_face_landmarks') and landmarks.multi_face_landmarks:
                    lms = landmarks.multi_face_landmarks[0].landmark
                if idx < len(lms):
                    pt = lms[idx]
                    return pt.x * w, pt.y * h
        return None

    def calculate_distance(self, pt1_id, pt2_id, landmarks, pose_landmarks, face_dim, body_dim):
        c1 = self.get_landmark_coords(pt1_id, landmarks, pose_landmarks, face_dim, body_dim)
        c2 = self.get_landmark_coords(pt2_id, landmarks, pose_landmarks, face_dim, body_dim)
        if c1 is None or c2 is None:
            return None
        return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

    def evaluate_custom_pattern(self, pt1_id, pt2_id, op, threshold_val, landmarks, pose_landmarks, baselines, current_eye_distance, current_shoulder_width, face_dim, body_dim):
        if not baselines:
            return False
            
        # Retrieve baseline landmarks lists
        base_face = baselines.get("face_landmarks")
        base_pose = baselines.get("pose_landmarks")
        
        # Calculate baseline distance between the points
        d_base = self.calculate_distance(pt1_id, pt2_id, base_face, base_pose, face_dim, body_dim)
        if d_base is None or d_base == 0:
            return False
            
        # Calculate current distance between the points
        d_curr = self.calculate_distance(pt1_id, pt2_id, landmarks, pose_landmarks, face_dim, body_dim)
        if d_curr is None:
            return False
            
        # Determine zoom/depth scaling factor
        # Check if both target points are pose landmarks
        def is_pose_id(pid):
            if pid.startswith('p'):
                return True
            if pid.startswith('f'):
                return False
            try:
                return int(pid) <= 32
            except Exception:
                return False
                
        is_pt1_pose = is_pose_id(pt1_id)
        is_pt2_pose = is_pose_id(pt2_id)
        
        scale = 1.0
        if is_pt1_pose and is_pt2_pose and baselines.get("shoulder_width", 0.0) > 0 and current_shoulder_width > 0:
            scale = baselines["shoulder_width"] / current_shoulder_width
        elif baselines.get("eye_distance", 0.0) > 0 and current_eye_distance > 0:
            scale = baselines["eye_distance"] / current_eye_distance
            
        d_curr_normalized = d_curr * scale
        change = (d_curr_normalized - d_base) / d_base
        threshold = threshold_val / 100.0
        
        if op == "><":      # shrink
            return change <= -threshold
        elif op == "<>":    # expand
            return change >= threshold
        elif op == ">><<":  # both / change
            return abs(change) >= threshold
            
        return False

    def evaluate(self, active_skills_dict, landmarks=None, pose_landmarks=None, baselines=None, current_eye_distance=0.0, current_shoulder_width=0.0, face_dim=(640, 480), body_dim=(640, 480)):
        triggered_events = {}
        
        for evt_name, evt_config in self.events.items():
            syntax = evt_config.get("rule_syntax", "")
            if not syntax:
                # Compatibility fallback to rules list
                rules = evt_config.get("rules", [])
                if isinstance(rules, list) and len(rules) > 0:
                    syntax = rules[0]
                else:
                    triggered_events[evt_name] = False
                    continue
            
            # Find and evaluate custom patterns like: pt1,pt2 >< num=15%
            # Operator regex: >< (shrink), <> (expand), >><< (both)
            pattern_regex = r'([fp]?\d+)\s*,\s*([fp]?\d+)\s*(><|<>|>><<)\s*num=(\d+)(%)?'
            
            # We want to substitute each matching sub-expression with its True/False evaluation
            working_syntax = syntax
            matches = re.findall(pattern_regex, working_syntax)
            
            for pt1, pt2, op, num_str, pct in matches:
                # Reconstruct full string to replace
                full_pattern = f"{pt1},{pt2}{op}num={num_str}"
                if pct:
                    full_pattern += pct
                # Handle flexible spacing around operator and comma for replacement matching
                full_pattern_escaped = re.escape(pt1) + r'\s*,\s*' + re.escape(pt2) + r'\s*' + re.escape(op) + r'\s*num=' + re.escape(num_str) + (r'%' if pct else '')
                
                # Evaluate the individual custom rule
                eval_bool = self.evaluate_custom_pattern(
                    pt1, pt2, op, float(num_str),
                    landmarks, pose_landmarks, baselines,
                    current_eye_distance, current_shoulder_width,
                    face_dim, body_dim
                )
                
                # Replace pattern in working syntax
                working_syntax = re.sub(full_pattern_escaped, "True" if eval_bool else "False", working_syntax)

            # Now replace standard logical operators (case-insensitive)
            py_syntax = re.sub(r'\bAND\b', 'and', working_syntax, flags=re.IGNORECASE)
            py_syntax = re.sub(r'\bOR\b', 'or', py_syntax, flags=re.IGNORECASE)
            py_syntax = re.sub(r'\bNOT\b', 'not', py_syntax, flags=re.IGNORECASE)
            
            # Replace remaining variables (like slouch, sway, etc.)
            def replacer(match):
                word = match.group(0)
                if word.lower() in ('and', 'or', 'not', 'true', 'false'):
                    return word
                # Check if it's in active_skills_dict
                if word in active_skills_dict and active_skills_dict[word]:
                    return "True"
                return "False"
                
            py_syntax = re.sub(r'[a-zA-Z0-9_]+', replacer, py_syntax)
            
            try:
                # Evaluate the final logic expression safely
                result = eval(py_syntax, {"__builtins__": {}}, {})
                triggered_events[evt_name] = bool(result)
            except Exception as e:
                self.logger.warning(f"Failed to evaluate event '{evt_name}' syntax '{syntax}' (compiled: '{py_syntax}'): {e}")
                triggered_events[evt_name] = False
                
        return triggered_events
