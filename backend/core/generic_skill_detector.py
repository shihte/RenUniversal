"""
通用技能偵測器 (Generic Skill Detector)
供沒有 logic.py 的 UI 建立技能使用。
讀取 config.json 中的 rule_syntax，解析點位距離語法並執行判定。

語法格式: pt1,pt2 >< num=20%
  - pt1, pt2: 點位 ID (p0-p32 為身體, f0-f467 為臉部)
  - 運算子: >< 縮短 | <> 放大 | >><< 變化 | ~~ 震動
  - num=N%: 閾值百分比
"""
import re
import math
from typing import Tuple, Dict, Any, Optional


class GenericActionDetector:
    """
    通用點位距離技能偵測器。
    由 ActionEngine 自動分配給沒有自訂 logic.py 的 UI 技能。
    """

    RULE_PATTERN = re.compile(
        r'([fp]?\d+)\s*,\s*([fp]?\d+)\s*(><|<>|>><<|~~)\s*num=(\d+(?:\.\d+)?)(%|px)?',
        re.IGNORECASE
    )

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 支援字串或舊格式 rules list
        raw_rules = config.get("rules", [])
        if isinstance(raw_rules, list) and len(raw_rules) > 0 and isinstance(raw_rules[0], str):
            self.rule_syntax = raw_rules[0]
        else:
            self.rule_syntax = config.get("rule_syntax", "")
        self.dist_history = {}
        self.capsules_to_draw = []

    def get_used_points(self) -> set:
        pts = set()
        for m in self.RULE_PATTERN.finditer(self.rule_syntax):
            pts.add(m.group(1).lower())
            pts.add(m.group(2).lower())
        return pts

    def get_point_pairs(self) -> list:
        pairs = []
        for m in self.RULE_PATTERN.finditer(self.rule_syntax):
            pairs.append((m.group(1).lower(), m.group(2).lower()))
        return pairs

    def _get_coord(self, pt_id: str, face_lm, pose_lm, face_dim, body_dim, baseline=False):
        """把點位 ID 轉成像素座標。"""
        pt_id = str(pt_id).strip().lower()
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
                v = int(pt_id)
                is_pose = (v <= 32)
            except ValueError:
                return None

        try:
            idx = int(idx_str)
        except ValueError:
            return None

        if is_pose:
            lm = pose_lm
            w, h = body_dim
        else:
            lm = face_lm
            w, h = face_dim

        if lm is None:
            return None

        try:
            if baseline:
                # baseline 是 list of dicts
                if isinstance(lm, list) and idx < len(lm):
                    pt = lm[idx]
                    return pt.get("x", 0.0) * w, pt.get("y", 0.0) * h
            else:
                # live mediapipe landmarks
                if hasattr(lm, 'landmark') and idx < len(lm.landmark):
                    pt = lm.landmark[idx]
                    return pt.x * w, pt.y * h
                elif isinstance(lm, list) and idx < len(lm):
                    pt = lm[idx]
                    if isinstance(pt, dict):
                        return pt.get("x", 0.0) * w, pt.get("y", 0.0) * h
                    else:
                        return pt.x * w, pt.y * h
        except Exception:
            pass
        return None

    def _dist(self, a, b):
        if a is None or b is None:
            return None
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _dist_to_segment(self, p, v, w):
        l2 = (w[0] - v[0])**2 + (w[1] - v[1])**2
        if l2 == 0:
            return self._dist(p, v)
        t = ((p[0] - v[0]) * (w[0] - v[0]) + (p[1] - v[1]) * (w[1] - v[1])) / l2
        t = max(0, min(1, t))
        proj = (v[0] + t * (w[0] - v[0]), v[1] + t * (w[1] - v[1]))
        return self._dist(p, proj)

    def _evaluate_pattern(self, pt1_id, pt2_id, op, num_str, pct_sign, face_landmarks, pose_landmarks, face_dim, body_dim, baselines, preferences):
        threshold = float(num_str)
        is_pct = (pct_sign == '%')
        if is_pct and op != "~~":
            threshold /= 100.0
        
        # Override with slider preference if available, but NOT if explicitly using px unit
        pref_key = f"{self.config.get('name', '')}_threshold"
        if pref_key in preferences and pct_sign != 'px':
            try:
                pref_val = float(preferences[pref_key])
                if op == "~~" or not is_pct:
                    # UI slider ALWAYS divides by 100 when saving (e.g., 100px saves as 1.0)
                    # So we need to multiply back by 100 to get the pixel value.
                    threshold = pref_val * 100.0
                else:
                    threshold = pref_val
            except ValueError:
                pass

        def is_pose_id(pid):
            pid = pid.lower()
            if pid.startswith('p'):
                return True
            if pid.startswith('f'):
                return False
            try:
                return int(pid) <= 32
            except Exception:
                return False

        pt1_pose = is_pose_id(pt1_id)
        pt2_pose = is_pose_id(pt2_id)

        base_face = baselines.get("face_landmarks")
        base_pose = baselines.get("pose_landmarks")

        c1 = self._get_coord(pt1_id, face_landmarks, pose_landmarks, face_dim, body_dim)
        c2 = self._get_coord(pt2_id, face_landmarks, pose_landmarks, face_dim, body_dim)
        d_curr = self._dist(c1, c2)

        b1 = self._get_coord(pt1_id, base_face, base_pose, face_dim, body_dim, baseline=True)
        b2 = self._get_coord(pt2_id, base_face, base_pose, face_dim, body_dim, baseline=True)
        d_base = self._dist(b1, b2)

        if d_curr is None or d_base is None or d_base == 0:
            return False, 0.0

        scale = 1.0
        # 應使用者要求：拿掉所有動態遠近補償，直接拿三秒初始值 (d_base) 當作 100% 進行比對。
        # 這樣最直覺，轉頭距離縮短就是縮短，不會被補償機制給抵消。

        if op == "~~":
            # 膠囊型震動檢測
            scaled_radius = threshold / scale
            dist1 = self._dist_to_segment(c1, b1, b2)
            dist2 = self._dist_to_segment(c2, b1, b2)
            
            # 只要線沒有100％在裡面 (即任一點出界) 就是晃動成立
            if dist1 > scaled_radius or dist2 > scaled_radius:
                triggered = True
                change = max(dist1, dist2) - scaled_radius
            else:
                triggered = False
                change = 0.0

            if hasattr(self, 'capsules_to_draw'):
                self.capsules_to_draw.append({
                    "b1": b1,
                    "b2": b2,
                    "radius": scaled_radius,
                    "triggered": triggered,
                    "pt1_id": pt1_id,
                    "pt2_id": pt2_id
                })
        else:
            d_norm = d_curr * scale
            change = (d_norm - d_base) / d_base

            if op == "><":
                triggered = change <= -threshold
            elif op == "<>":
                triggered = change >= threshold
            elif op.strip() == ">><<":
                triggered = abs(change) >= threshold
            else:
                triggered = False

        return triggered, float(change)


    def evaluate(self,
                 face_landmarks, pose_landmarks,
                 face_dim: Tuple[int, int], body_dim: Tuple[int, int],
                 baselines: Dict[str, float],
                 preferences: Dict[str, Any],
                 state_history: Dict[str, Any]) -> Tuple[bool, float, Dict[str, Any]]:

        info: Dict[str, Any] = {"rule_syntax": self.rule_syntax}
        
        matches = list(self.RULE_PATTERN.finditer(self.rule_syntax))
        if not matches:
            info["error"] = f"Cannot parse rule_syntax: {self.rule_syntax!r}"
            return False, 0.0, info

        working_syntax = self.rule_syntax
        max_change = 0.0
        self.capsules_to_draw = []

        for m in matches:
            pt1_id, pt2_id, op, num_str, pct_sign = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
            triggered, change = self._evaluate_pattern(
                pt1_id, pt2_id, op, num_str, pct_sign,
                face_landmarks, pose_landmarks, face_dim, body_dim, baselines, preferences
            )
            if abs(change) > abs(max_change):
                max_change = change
                
            full_pattern_escaped = re.escape(m.group(0))
            working_syntax = re.sub(full_pattern_escaped, "True" if triggered else "False", working_syntax, count=1)

        info["change_pct"] = round(max_change * 100, 1)

        py_syntax = re.sub(r'\bAND\b', 'and', working_syntax, flags=re.IGNORECASE)
        py_syntax = re.sub(r'\bOR\b', 'or', py_syntax, flags=re.IGNORECASE)
        py_syntax = py_syntax.replace('!', ' not ')
        
        def replacer(match):
            word = match.group(0)
            if word.lower() in ('and', 'or', 'not', 'true', 'false'):
                return word
            return "False"
            
        py_syntax = re.sub(r'[a-zA-Z0-9_]+', replacer, py_syntax)
        
        try:
            result = eval(py_syntax, {"__builtins__": {}}, {})
            final_trigger = bool(result)
        except Exception as e:
            info["error"] = f"Eval failed for {py_syntax}: {e}"
            final_trigger = False

        return final_trigger, max_change, info
