"""
地標座標工具 (Landmark Coordinate Utility)

提供統一的點位 ID 解析與像素座標轉換，
供 GenericSkillDetector 與 EventEngine 共用，消除重複實作。

點位語法：
  f0–f477   臉部地標 (FaceLandmarker)
  p0–p32    姿態地標 (PoseLandmarker)
  純數字 ≤32 視為姿態，>32 視為臉部
"""
from typing import Optional, Tuple, Any


def get_landmark_coord(
    pt_id: str,
    face_lm: Any,
    pose_lm: Any,
    face_dim: Tuple[int, int],
    body_dim: Tuple[int, int],
    baseline: bool = False,
) -> Optional[Tuple[float, float]]:
    """把點位 ID 轉成像素座標。

    Args:
        pt_id:     點位識別字串，如 'f1', 'p11', '152'
        face_lm:   臉部地標（MediaPipe 物件或 baseline list of dicts）
        pose_lm:   姿態地標（同上）
        face_dim:  臉部影格 (width, height)
        body_dim:  姿態影格 (width, height)
        baseline:  True 表示傳入的是 list of dicts（校正基準），
                   False 表示傳入 MediaPipe 即時推論物件

    Returns:
        (x, y) 像素座標，無法解析時回傳 None
    """
    pt_id = str(pt_id).strip().lower()
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

    lm = pose_lm if is_pose else face_lm
    w, h = body_dim if is_pose else face_dim

    if lm is None:
        return None

    try:
        if baseline:
            if isinstance(lm, list) and idx < len(lm):
                pt = lm[idx]
                return pt.get("x", 0.0) * w, pt.get("y", 0.0) * h
        else:
            # 支援 MediaPipe legacy solutions (multi_face_landmarks) 與 Tasks API
            if hasattr(lm, 'multi_face_landmarks') and lm.multi_face_landmarks:
                lm = lm.multi_face_landmarks[0].landmark
            elif hasattr(lm, 'landmark'):
                lm = lm.landmark

            if isinstance(lm, list) and idx < len(lm):
                pt = lm[idx]
                if isinstance(pt, dict):
                    return pt.get("x", 0.0) * w, pt.get("y", 0.0) * h
                return pt.x * w, pt.y * h
    except Exception:
        pass
    return None
