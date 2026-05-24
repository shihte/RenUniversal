"""
通用技能偵測器 (Generic Skill Detector)
供沒有 logic.py 的 UI 建立技能使用。
讀取 config.json 中的 rule_syntax，解析點位距離語法並執行判定。

語法格式: pt1,pt2 >< num=20%
  - pt1, pt2: 點位 ID (p0-p32 為身體, f0-f467 為臉部)
  - 運算子: >< 縮短 | <> 放大 | >><< 變化
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
        r'([fp]?\d+)\s*,\s*([fp]?\d+)\s*(><|<>|>><<)\s*num=(\d+(?:\.\d+)?)%?',
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

    def get_used_points(self) -> set:
        m = self.RULE_PATTERN.search(self.rule_syntax)
        if m:
            return {m.group(1).lower(), m.group(2).lower()}
        return set()

    def get_point_pairs(self) -> list:
        m = self.RULE_PATTERN.search(self.rule_syntax)
        if m:
            return [(m.group(1).lower(), m.group(2).lower())]
        return []

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

    def evaluate(self,
                 face_landmarks, pose_landmarks,
                 face_dim: Tuple[int, int], body_dim: Tuple[int, int],
                 baselines: Dict[str, float],
                 preferences: Dict[str, Any],
                 state_history: Dict[str, Any]) -> Tuple[bool, float, Dict[str, Any]]:

        info: Dict[str, Any] = {"rule_syntax": self.rule_syntax}

        m = self.RULE_PATTERN.search(self.rule_syntax)
        if not m:
            info["error"] = f"Cannot parse rule_syntax: {self.rule_syntax!r}"
            return False, 0.0, info

        pt1_id, pt2_id, op, num_str = m.group(1), m.group(2), m.group(3), m.group(4)
        threshold = float(num_str) / 100.0
        
        # Override with slider preference if available
        pref_key = f"{self.config.get('name', '')}_threshold"
        if pref_key in preferences:
            try:
                threshold = float(preferences[pref_key])
            except ValueError:
                pass

        # 判斷是否為 pose 點（決定要用哪組 baseline）
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

        # 當前距離
        c1 = self._get_coord(pt1_id, face_landmarks, pose_landmarks, face_dim, body_dim)
        c2 = self._get_coord(pt2_id, face_landmarks, pose_landmarks, face_dim, body_dim)
        d_curr = self._dist(c1, c2)

        # 基準距離
        b1 = self._get_coord(pt1_id, base_face, base_pose, face_dim, body_dim, baseline=True)
        b2 = self._get_coord(pt2_id, base_face, base_pose, face_dim, body_dim, baseline=True)
        d_base = self._dist(b1, b2)

        if d_curr is None or d_base is None or d_base == 0:
            info["error"] = "Points not found or baseline missing"
            return False, 0.0, info

        # 縮放補償（防止身體靠近鏡頭）
        scale = 1.0
        if pt1_pose and pt2_pose:
            sw = baselines.get("shoulder_width", 0.0)
            curr_sw = baselines.get("_current_shoulder_width", 0.0)
            if sw > 0 and curr_sw > 0:
                scale = sw / curr_sw
        else:
            ed = baselines.get("eye_distance", 0.0)
            curr_ed = baselines.get("_current_eye_distance", 0.0)
            if ed > 0 and curr_ed > 0:
                scale = ed / curr_ed

        d_norm = d_curr * scale
        change = (d_norm - d_base) / d_base

        info["change_pct"] = round(change * 100, 1)
        info["threshold_pct"] = round(threshold * 100, 1)

        if op == "><":
            triggered = change <= -threshold
        elif op == "<>":
            triggered = change >= threshold
        elif op == ">><< ":
            triggered = abs(change) >= threshold
        else:
            triggered = False

        return triggered, float(change), info
