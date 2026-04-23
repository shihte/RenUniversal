"""
代理流水線核心 (Agent Pipeline Core)
負責協調整合各項技能，驅動整體的影像處理、姿勢分析與數據更新。
"""

import cv2
import mediapipe as mp
import time
import numpy as np
import math
from loguru import logger
from typing import Optional, Dict, Any, Tuple

from .state import SharedState
from skills.video_capture.logic import VideoCaptureSkill
from skills.video_capture.schema import CaptureConfig
from skills.posture_reviewer.logic import PostureReviewerSkill
from skills.calibration_wizard.logic import CalibrationWizardSkill

class AgentPipeline:
    """
    實作代理流水線 (Pipeline Pattern)。
    
    該類別作為中央協調器，從 VideoCapture 讀取影格，交由 MediaPipe 提取地標，
    隨後調用 CalibrationWizard 或 PostureReviewer 進行分析，最終將狀態同步至 SharedState。
    """
    
    def __init__(self, state: SharedState):
        """
        初始化代理流水線。
        
        Args:
            state (SharedState): 全局共享狀態，用於跨線程與前端通訊。
        """
        self.state = state
        
        # 1. 初始化各項技能 (Skill Initialization)
        self.capture = VideoCaptureSkill(CaptureConfig(src=0)).start()
        self.reviewer = PostureReviewerSkill()
        self.wizard = CalibrationWizardSkill()
        
        # 2. MediaPipe 模型設定
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 3. 運行時基礎數據
        self.baseline_eye_distance = 0.0
        self.baseline_nose_chin_distance = 0.0
        self.is_calibrated = False
        self.is_down_previously = False
        
        logger.info("AgentPipeline initialized and ready for execution")

    def _extract_physical_features(self, landmarks: Any, width: int, height: int) -> Tuple[float, float]:
        """
        從地標數據中提取關鍵物理距離（眼距與鼻尖至下巴距離）。
        
        Args:
            landmarks (Any): 面部地標集合。
            width (int): 影格寬度。
            height (int): 影格高度。
            
        Returns:
            Tuple[float, float]: (當前眼距, 當前鼻尖至下巴距離)。
        """
        # 定義地標索引
        NOSE_INDEX, CHIN_INDEX = 1, 152
        LEFT_EYE_INDEX, RIGHT_EYE_INDEX = 33, 263
        
        nose = landmarks.landmark[NOSE_INDEX]
        chin = landmarks.landmark[CHIN_INDEX]
        left_eye = landmarks.landmark[LEFT_EYE_INDEX]
        right_eye = landmarks.landmark[RIGHT_EYE_INDEX]
        
        # 轉換為像素距離
        current_eye_distance = abs(right_eye.x * width - left_eye.x * width)
        current_nose_chin_distance = math.sqrt(
            (nose.x * width - chin.x * width)**2 + 
            (nose.y * height - chin.y * height)**2
        )
        
        return current_eye_distance, current_nose_chin_distance

    def _annotate_frame(self, frame: np.ndarray, landmarks: Any, width: int, height: int, status: Any) -> None:
        """
        在畫面上繪製追蹤點與狀態資訊。
        """
        # 1. 定義關鍵點索引與顏色
        NOSE_INDEX, CHIN_INDEX = 1, 152
        LEFT_EYE_INDEX, RIGHT_EYE_INDEX = 33, 263
        
        points = [
            (landmarks.landmark[NOSE_INDEX], (255, 100, 0), "Nose"),      # 藍色 (BGR)
            (landmarks.landmark[CHIN_INDEX], (0, 0, 255), "Chin"),        # 紅色
            (landmarks.landmark[LEFT_EYE_INDEX], (0, 255, 0), "L-Eye"),    # 綠色
            (landmarks.landmark[RIGHT_EYE_INDEX], (0, 255, 0), "R-Eye")    # 綠色
        ]

        # 2. 繪製追蹤點
        for lm, color, label in points:
            cx, cy = int(lm.x * width), int(lm.y * height)
            cv2.circle(frame, (cx, cy), 5, color, -1)
            cv2.circle(frame, (cx, cy), 7, (255, 255, 255), 1)

        # 3. 繪製鼻尖到下巴的連線 (姿勢參考線)
        nose = landmarks.landmark[NOSE_INDEX]
        chin = landmarks.landmark[CHIN_INDEX]
        cv2.line(frame, 
                 (int(nose.x * width), int(nose.y * height)), 
                 (int(chin.x * width), int(chin.y * height)), 
                 (255, 255, 255), 1, cv2.LINE_AA)

        # 4. 繪製狀態文字
        status_text = "CALIBRATING..." if status.calibrating else f"RATIO: {status.ratio}%"
        color = (255, 255, 255)
        if not status.calibrating:
            if status.is_bad_posture:
                status_text += " [BAD POSTURE]"
                color = (0, 0, 255)
            elif status.is_turning:
                status_text += " [TURNING]"
                color = (0, 255, 255)
            else:
                status_text += " [GOOD]"
                color = (0, 255, 0)
        
        # 陰影文字增加可讀性
        display_y = 40
        cv2.putText(frame, status_text, (20, display_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, status_text, (20, display_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1, cv2.LINE_AA)
        
        # 顯示延遲與計數
        info_text = f"Lat: {status.latency_ms}ms | Down: {status.down_count}"
        cv2.putText(frame, info_text, (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, info_text, (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        if status.calibrating:
            progress_bar_w = int(width * 0.6 * status.calibration_progress / 100)
            cv2.rectangle(frame, (20, 60), (20 + int(width * 0.6), 75), (50, 50, 50), -1)
            cv2.rectangle(frame, (20, 60), (20 + progress_bar_w, 75), (0, 255, 0), -1)

    def run_cycle(self) -> Optional[np.ndarray]:
        """
        執行單一流水線循環（Cycle）。
        
        包含了：讀取 -> 推理 -> (校準或審查) -> 狀態寫回 -> 畫面處理。
        
        Returns:
            Optional[np.ndarray]: 處理後的可視化影格，若無法讀取則傳回 None。
        """
        # 1. 擷取階段 (Tool Wrapper)
        frame_data = self.capture.read()
        if not frame_data.grabbed or frame_data.frame is None:
            return None

        frame = frame_data.frame
        height, width, _ = frame.shape
        
        # 2. 特徵提取階段 (Inference)
        inference_start = time.perf_counter()
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inference_results = self.face_mesh.process(image_rgb)
        inference_time_ms = int((time.perf_counter() - inference_start) * 1000)
        
        landmarks = inference_results.multi_face_landmarks[0] if inference_results.multi_face_landmarks else None
        
        if landmarks:
            # 輔助計算物理特徵
            eye_dist, nc_dist = self._extract_physical_features(landmarks, width, height)

            # 3. 邏輯決策階段
            if not self.is_calibrated:
                # 模式 A: 校準 (Inversion Pattern)
                calibration_result = self.wizard.process(eye_dist, nc_dist)
                self.state.update_status(
                    calibrating=True,
                    calibration_progress=calibration_result.progress
                )
                
                if calibration_result.is_complete:
                    self.baseline_eye_distance = calibration_result.baseline_eye_dist
                    self.baseline_nose_chin_distance = calibration_result.baseline_nc_dist
                    self.is_calibrated = True
                    logger.success(f"Calibration successful: Baseline NC Dist = {self.baseline_nose_chin_distance:.1f}")
            else:
                # 模式 B: 姿勢審查 (Reviewer Pattern)
                posture_report = self.reviewer.evaluate(
                    landmarks, width, height,
                    self.baseline_eye_distance,
                    self.baseline_nose_chin_distance,
                    self.state.get_status().is_bad_posture
                )
                
                if posture_report.is_valid:
                    metrics = posture_report.metrics
                    # 偵測低頭次數 (邊緣觸發：從端正變為不良)
                    current_down_count = self.state.get_status().down_count
                    if metrics.is_bad_posture and not self.is_down_previously:
                        current_down_count += 1
                    
                    self.is_down_previously = metrics.is_bad_posture

                    # 狀態同步 (Observability)
                    self.state.update_status(
                        ratio=float(round(metrics.nc_ratio * 100, 1)),
                        is_bad_posture=metrics.is_bad_posture,
                        is_turning=metrics.is_turning,
                        down_count=current_down_count,
                        latency_ms=inference_time_ms,
                        calibrating=False
                    )
            
            # 視覺標註階段 (Visualization)
            self._annotate_frame(frame, landmarks, width, height, self.state.get_status())
        else:
            # 即使沒偵測到人臉，也更新延遲數值
            self.state.update_status(latency_ms=inference_time_ms)

        # 5. 輸出渲染 (MJPEG 格式前置處理)
        return cv2.flip(frame, 1)

    def stop(self) -> None:
        """安全停止流水線並釋放資源。"""
        logger.info("Stopping AgentPipeline workflow")
        self.capture.stop()
