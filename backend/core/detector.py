import cv2
import mediapipe.python.solutions.face_mesh as mp_face_mesh
import numpy as np
import time
import math
from typing import Dict, Any, Tuple, Optional, List
from .state import SharedState

class PostureDetector:
    """
    負責姿勢檢測的核心推理邏輯。
    包含校準相位、偏航 (Yaw) 過濾與低頭判定。
    """
    def __init__(self, state: SharedState, threshold_ratio: float = 0.20, yaw_tolerance: float = 0.10):
        self.state = state
        self.threshold_ratio = threshold_ratio
        self.yaw_tolerance = yaw_tolerance
        
        # MediaPipe 初始化
        self.mp_face_mesh = mp_face_mesh
        
        # 校準設定
        self.calibration_duration: float = 3.0
        self.calibration_start_time: Optional[float] = None
        self.is_calibrated: bool = False
        self.baseline_eye_dist: float = 0.0
        self.baseline_nose_chin_dist: float = 0.0
        self.calib_samples_eye: List[float] = []
        self.calib_samples_nose_chin: List[float] = []
        
        # 狀態計數
        self.down_count: int = 0
        self.is_down: bool = False
        self.is_turning: bool = False
        
        # 推理優化與平滑
        self.prev_time: float = 0.0
        self.smooth_nose_chin: float = 0.0
        self.alpha: float = 0.3
        self.smooth_latency: float = 0.0
        self.latency_alpha: float = 0.1
        
        # 地標索引 (Landmark Indices)
        self.NOSE = 1
        self.CHIN = 152
        self.LEFT_EYE = 33
        self.RIGHT_EYE = 263

    def calculate_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """計算兩點間的歐幾里得距離。"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def get_metrics(self, face_landmarks: Any, w: int, h: int) -> Dict[str, Any]:
        """擷取關鍵點坐標並計算距離度量。"""
        # 獲取標準化點位
        nose = face_landmarks.landmark[self.NOSE]
        chin = face_landmarks.landmark[self.CHIN]
        left_eye = face_landmarks.landmark[self.LEFT_EYE]
        right_eye = face_landmarks.landmark[self.RIGHT_EYE]
        
        # 轉換為像素坐標
        nose_pt = (nose.x * w, nose.y * h)
        chin_pt = (chin.x * w, chin.y * h)
        left_eye_pt = (left_eye.x * w, left_eye.y * h)
        right_eye_pt = (right_eye.x * w, right_eye.y * h)
        
        # 計算距離
        eye_horiz_dist = abs(right_eye_pt[0] - left_eye_pt[0])
        nose_chin_dist = self.calculate_distance(nose_pt, chin_pt)
        
        return {
            "eye_dist": eye_horiz_dist,
            "nose_chin_dist": nose_chin_dist,
            "points": (nose_pt, chin_pt, left_eye_pt, right_eye_pt)
        }

    def process_frame(self, frame: np.ndarray, face_mesh: Any) -> np.ndarray:
        """
        處理單幀影像，執行推理並標註結果。
        """
        h, w, _ = frame.shape
        inference_w, inference_h = 640, 360
        
        # 優化：推理前縮小尺寸
        frame_small = cv2.resize(frame, (inference_w, inference_h))
        img_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        
        start_time = time.time()
        results = face_mesh.process(img_rgb)
        
        is_bad = False
        nc_ratio = 0.0
        calib_prog = 0
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            metrics = self.get_metrics(landmarks, w, h)
            
            eye_dist = metrics["eye_dist"]
            nc_dist = metrics["nose_chin_dist"]
            nose_pt, chin_pt, le_pt, re_pt = metrics["points"]

            # --- 校準階段 (Calibration Phase) ---
            if not self.is_calibrated:
                if self.calibration_start_time is None:
                    self.calibration_start_time = time.time()
                
                elapsed = time.time() - self.calibration_start_time
                calib_prog = min(elapsed / self.calibration_duration, 1.0)
                
                self.calib_samples_eye.append(eye_dist)
                self.calib_samples_nose_chin.append(nc_dist)
                
                # 繪製 UI
                self._draw_calibration_ui(frame, calib_prog, w, h)
                
                if elapsed >= self.calibration_duration:
                    self.baseline_eye_dist = float(np.mean(self.calib_samples_eye))
                    self.baseline_nose_chin_dist = float(np.mean(self.calib_samples_nose_chin))
                    # 防止除以零
                    if self.baseline_eye_dist == 0: self.baseline_eye_dist = 1.0
                    if self.baseline_nose_chin_dist == 0: self.baseline_nose_chin_dist = 1.0
                    self.is_calibrated = True
            
            # --- 檢測階段 (Detection Phase) ---
            else:
                # 偏航過濾 (Yaw Filtering)
                deviation = abs(eye_dist - self.baseline_eye_dist) / self.baseline_eye_dist
                self.is_turning = deviation > self.yaw_tolerance
                
                # 平滑處理
                if self.smooth_nose_chin == 0:
                    self.smooth_nose_chin = nc_dist
                else:
                    self.smooth_nose_chin = self.alpha * nc_dist + (1 - self.alpha) * self.smooth_nose_chin
                
                # 計算比例
                nc_ratio = (self.smooth_nose_chin - self.baseline_nose_chin_dist) / self.baseline_nose_chin_dist
                
                # 繪製視覺化地標 (Visual Landmarks)
                color = (0, 255, 255) if self.is_turning else (0, 255, 0)
                self._draw_landmarks(frame, metrics["points"], color)
                
                if not self.is_turning:
                    if self.is_down:
                        if nc_ratio > -self.threshold_ratio + 0.05: # 磁滯效應 (Hysteresis)
                            self.is_down = False
                        else:
                            is_bad = True
                    else:
                        if nc_ratio < -self.threshold_ratio:
                            is_bad = True
                            self.down_count += 1
                            self.is_down = True

        # --- 計算效能指標 (Metrics) ---
        now = time.time()
        latency = (now - start_time) * 1000
        self.smooth_latency = self.latency_alpha * latency + (1 - self.latency_alpha) * self.smooth_latency
        fps = 1 / (now - self.prev_time) if self.prev_time else 0
        self.prev_time = now
        
        # 更新共享狀態
        self.state.update_status({
            "ratio": float(round(nc_ratio * 100, 1)),
            "nose_chin_ratio": float(round(nc_ratio, 3)),
            "is_bad_posture": bool(is_bad),
            "down_count": int(self.down_count),
            "fps": int(fps),
            "calibrating": not self.is_calibrated,
            "calibration_progress": int(calib_prog * 100),
            "is_turning": self.is_turning,
            "baseline_eye_dist": round(self.baseline_eye_dist, 1),
            "latency_ms": int(self.smooth_latency)
        })
        
        return cv2.flip(frame, 1)

    def _draw_calibration_ui(self, frame: np.ndarray, progress: float, w: int, h: int) -> None:
        """繪製校準中的 UI 層。"""
        cv2.putText(frame, f"Calibrating... {int(progress * 100)}%", 
                   (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
        cv2.putText(frame, "Please look straight ahead", 
                   (50, 90), cv2.FONT_HERSHEY_PLAIN, 1.5, (200, 200, 200), 2)
        
        # 進度條 (Progress Bar)
        bw = int(w * 0.6)
        bx = int((w - bw) / 2)
        by = h - 50
        cv2.rectangle(frame, (bx, by), (bx + bw, by + 20), (100, 100, 100), -1)
        cv2.rectangle(frame, (bx, by), (bx + int(bw * progress), by + 20), (0, 255, 0), -1)

    def _draw_landmarks(self, frame: np.ndarray, pts: Tuple, color: Tuple[int, int, int]) -> None:
        """在 Frame 上繪製點位。"""
        n, c, le, re = pts
        cv2.circle(frame, (int(n[0]), int(n[1])), 5, (0, 255, 255), -1)
        cv2.circle(frame, (int(c[0]), int(c[1])), 5, color, -1)
        cv2.line(frame, (int(n[0]), int(n[1])), (int(c[0]), int(c[1])), color, 2)
        cv2.line(frame, (int(le[0]), int(le[1])), (int(re[0]), int(re[1])), (255, 0, 0), 2)

    def recalibrate(self) -> None:
        """重置校準狀態。"""
        self.is_calibrated = False
        self.calibration_start_time = None
        self.calib_samples_eye = []
        self.calib_samples_nose_chin = []
