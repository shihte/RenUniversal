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
from backend.services.video_capture.logic import VideoCaptureSkill
from backend.services.video_capture.schema import CaptureConfig
from backend.services.calibration_wizard.logic import CalibrationWizardSkill
from .action_engine import ActionEngine

class AgentPipeline:
    """
    實作代理流水線 (Pipeline Pattern)。
    
    該類別作為中央協調器，從 VideoCapture 讀取影格，交由 MediaPipe 提取地標，
    隨後調用 CalibrationWizard 或 ActionEngine 進行分析，最終將狀態同步至 SharedState。
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
        self.action_engine = ActionEngine(skills_dir="skills")
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
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 3. 運行時基礎數據
        self.baseline_eye_distance = 0.0
        self.baseline_nose_chin_distance = 0.0
        self.baseline_shoulder_width = 0.0
        self.baseline_shoulder_midpoint_x = 0.0
        self.baseline_shoulder_midpoint_y = 0.0
        self.is_calibrated = False
        self.is_down_previously = False
        
        logger.info("AgentPipeline initialized and ready for execution")

    def _evaluate_posture(self, landmarks: Any, pose_landmarks: Any, face_dim: Tuple[int, int], body_dim: Tuple[int, int], inference_time_ms: int):
        """
        利用 ActionEngine 對當前所有姿態動作判斷包進行評估，並將狀態同步至 SharedState。
        """
        baselines = {
            "eye_distance": self.baseline_eye_distance,
            "nose_chin_distance": self.baseline_nose_chin_distance,
            "shoulder_width": self.baseline_shoulder_width,
            "shoulder_midpoint_x": self.baseline_shoulder_midpoint_x,
            "shoulder_midpoint_y": self.baseline_shoulder_midpoint_y
        }
        
        status = self.state.get_status()
        state_history = {
            "is_bad_posture": status.is_bad_posture,
            "is_swaying": status.is_swaying,
            "is_leaning_forward": status.is_leaning_forward
        }
        
        # 執行動作引擎評估
        results = self.action_engine.evaluate_all(
            landmarks, pose_landmarks, face_dim, body_dim, baselines, self.state.prefs, state_history
        )
        
        # 提取各模組結果
        is_bad_posture, nc_ratio, slouch_debug = results.get("slouch", (False, 0.0, {}))
        is_swaying, sway_ratio, sway_debug = results.get("sway", (False, 0.0, {}))
        is_leaning_forward, lean_ratio, lean_debug = results.get("lean", (False, 0.0, {}))
        
        is_turning = slouch_debug.get("is_turning", False)
        
        # 計算低頭次數
        current_down_count = status.down_count
        if is_bad_posture and not self.is_down_previously:
            current_down_count += 1
        self.is_down_previously = is_bad_posture
        
        # 更新共享狀態
        self.state.update_status(
            ratio=float(round(nc_ratio * 100, 1)),
            is_bad_posture=is_bad_posture,
            is_turning=is_turning,
            down_count=current_down_count,
            latency_ms=inference_time_ms,
            calibrating=False,
            is_swaying=is_swaying,
            is_leaning_forward=is_leaning_forward,
            sway_ratio=float(round(sway_ratio, 3)),
            lean_ratio=float(round(lean_ratio, 3))
        )

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

    def _extract_shoulder_features(self, pose_landmarks: Any, width: int, height: int) -> Tuple[float, float, float]:
        """
        從 Pose 地標中提取肩膀寬度、中點 X 與 Y 座標（像素）。
        """
        left_shoulder = pose_landmarks.landmark[11]
        right_shoulder = pose_landmarks.landmark[12]
        
        ls_x, ls_y = left_shoulder.x * width, left_shoulder.y * height
        rs_x, rs_y = right_shoulder.x * width, right_shoulder.y * height
        
        sh_width = math.sqrt((ls_x - rs_x)**2 + (ls_y - rs_y)**2)
        sh_mid_x = (ls_x + rs_x) / 2.0
        sh_mid_y = (ls_y + rs_y) / 2.0
        
        return sh_width, sh_mid_x, sh_mid_y

    def _annotate_frame(self, frame: np.ndarray, landmarks: Any, width: int, height: int, status: Any, pose_landmarks: Any = None, draw_text: bool = True) -> None:
        """
        在畫面上繪製追蹤點與狀態資訊。
        """
        NOSE_INDEX, CHIN_INDEX = 1, 152
        LEFT_EYE_INDEX, RIGHT_EYE_INDEX = 33, 263
        
        # 1. 繪製面部追蹤點
        if landmarks is not None:
            points = [
                (landmarks.landmark[NOSE_INDEX], (255, 100, 0), "Nose"),      # 藍色 (BGR)
                (landmarks.landmark[CHIN_INDEX], (0, 0, 255), "Chin"),        # 紅色
                (landmarks.landmark[LEFT_EYE_INDEX], (0, 255, 0), "L-Eye"),    # 綠色
                (landmarks.landmark[RIGHT_EYE_INDEX], (0, 255, 0), "R-Eye")    # 綠色
            ]
            for lm, color, label in points:
                cx, cy = int(lm.x * width), int(lm.y * height)
                cv2.circle(frame, (cx, cy), 5, color, -1)
                cv2.circle(frame, (cx, cy), 7, (255, 255, 255), 1)

            # 2. 繪製鼻尖到下巴的連線 (姿勢參考線)
            nose = landmarks.landmark[NOSE_INDEX]
            chin = landmarks.landmark[CHIN_INDEX]
            cv2.line(frame, 
                     (int(nose.x * width), int(nose.y * height)), 
                     (int(chin.x * width), int(chin.y * height)), 
                     (255, 255, 255), 1, cv2.LINE_AA)

        # 3. 繪製肩膀與連結線
        if pose_landmarks:
            left_shoulder = pose_landmarks.landmark[11]
            right_shoulder = pose_landmarks.landmark[12]
            
            ls_x, ls_y = int(left_shoulder.x * width), int(left_shoulder.y * height)
            rs_x, rs_y = int(right_shoulder.x * width), int(right_shoulder.y * height)
            
            # 判斷顏色：若有任何肩膀不良姿勢（搖晃或前傾），顯示紅色，否則顯示綠色
            sh_color = (0, 0, 255) if (status.is_swaying or status.is_leaning_forward) else (0, 255, 0)
            
            cv2.circle(frame, (ls_x, ls_y), 6, sh_color, -1)
            cv2.circle(frame, (rs_x, rs_y), 6, sh_color, -1)
            cv2.circle(frame, (ls_x, ls_y), 8, (255, 255, 255), 1)
            cv2.circle(frame, (rs_x, rs_y), 8, (255, 255, 255), 1)
            
            # 連接肩膀
            cv2.line(frame, (ls_x, ls_y), (rs_x, rs_y), sh_color, 2, cv2.LINE_AA)
            
            # 繪製肩膀中點
            mid_x, mid_y = int((ls_x + rs_x) / 2), int((ls_y + rs_y) / 2)
            cv2.circle(frame, (mid_x, mid_y), 4, (255, 255, 255), -1)
        elif landmarks:
            # 繪製虛擬預估肩膀 (使用半透明/Cyan 藍繪製，提供使用者直觀的視覺回饋)
            left_eye_l = landmarks.landmark[LEFT_EYE_INDEX]
            right_eye_l = landmarks.landmark[RIGHT_EYE_INDEX]
            left_eye_p = (left_eye_l.x * width, left_eye_l.y * height)
            right_eye_p = (right_eye_l.x * width, right_eye_l.y * height)
            
            eye_dist = abs(right_eye_p[0] - left_eye_p[0])
            face_center_x = (left_eye_p[0] + right_eye_p[0]) / 2.0
            face_center_y = (left_eye_p[1] + right_eye_p[1]) / 2.0
            
            if self.is_calibrated and self.baseline_eye_distance > 0 and self.baseline_shoulder_width > 0:
                ratio = self.baseline_shoulder_width / self.baseline_eye_distance
                sh_width = eye_dist * ratio
            else:
                sh_width = eye_dist * 4.5
                
            sh_mid_x = face_center_x
            sh_mid_y = face_center_y + eye_dist * 3.0
            
            ls_x, ls_y = int(sh_mid_x - sh_width / 2.0), int(sh_mid_y)
            rs_x, rs_y = int(sh_mid_x + sh_width / 2.0), int(sh_mid_y)
            
            # 虛擬肩膀顏色：搖晃或前傾時顯示橘紅，否則顯示青藍色 (BGR 格式)
            sh_color = (0, 140, 255) if (status.is_swaying or status.is_leaning_forward) else (255, 191, 0)
            
            cv2.circle(frame, (ls_x, ls_y), 4, sh_color, -1)
            cv2.circle(frame, (rs_x, rs_y), 4, sh_color, -1)
            cv2.line(frame, (ls_x, ls_y), (rs_x, rs_y), sh_color, 1, cv2.LINE_AA)
            
            mid_x, mid_y = int((ls_x + rs_x) / 2), int((ls_y + rs_y) / 2)
            cv2.circle(frame, (mid_x, mid_y), 3, (255, 255, 255), -1)

        # 4. 繪製狀態文字 (如果啟用)
        if draw_text:
            status_text = "CALIBRATING..." if status.calibrating else f"RATIO: {status.ratio}%"
            color = (255, 255, 255)
            if not status.calibrating:
                alerts = []
                if status.is_bad_posture:
                    alerts.append("BAD POSTURE")
                if status.is_turning:
                    alerts.append("TURNING")
                if status.is_swaying:
                    alerts.append("SWAYING")
                if status.is_leaning_forward:
                    alerts.append("LEAN FORWARD")
                    
                if alerts:
                    status_text += " [" + " | ".join(alerts) + "]"
                    color = (0, 0, 255) if (status.is_bad_posture or status.is_swaying or status.is_leaning_forward) else (0, 255, 255)
                else:
                    status_text += " [GOOD]"
                    color = (0, 255, 0)
            
            # 陰影文字增加可讀性
            display_y = 40
            cv2.putText(frame, status_text, (20, display_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, status_text, (20, display_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1, cv2.LINE_AA)
            
            # 顯示延遲與計數及肩膀比例
            info_parts = [f"Lat: {status.latency_ms}ms", f"Down: {status.down_count}"]
            if not status.calibrating:
                info_parts.append(f"Sway: {status.sway_ratio*100:.1f}%")
                info_parts.append(f"Lean: {status.lean_ratio*100:.1f}%")
            info_text = " | ".join(info_parts)
            
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
        # 1. 擷取與切換鏡頭來源階段
        status = self.state.get_status()
        camera_source = getattr(status, "camera_source", "local_0")
        
        frame = None
        phone_frame = None
        is_dual = False
        
        if camera_source == "phone":
            net_frame, last_time = self.state.get_network_frame()
            if net_frame is not None and (time.time() - last_time) < 3.0:
                frame = net_frame.copy()
            else:
                # Fallback to local_0
                frame_data = self.capture.read()
                if frame_data.grabbed and frame_data.frame is not None:
                    frame = frame_data.frame.copy()
        elif camera_source == "dual":
            # 讀取電腦內置鏡頭
            frame_data = self.capture.read()
            local_frame = frame_data.frame.copy() if (frame_data.grabbed and frame_data.frame is not None) else None
            
            # 讀取手機鏡頭
            net_frame, last_time = self.state.get_network_frame()
            if net_frame is not None and (time.time() - last_time) < 3.0:
                phone_frame = net_frame.copy()
            
            if local_frame is not None and phone_frame is not None:
                is_dual = True
                # 預先對個別畫面進行鏡像翻轉，以利後續的左右一致性
                local_frame = cv2.flip(local_frame, 1)
                phone_frame = cv2.flip(phone_frame, 1)
            else:
                # Fallback to single frame (local or phone depending on what is available)
                if local_frame is not None:
                    frame = local_frame
                elif phone_frame is not None:
                    frame = phone_frame
        else:
            # 預設 Local 模式 ("local_0", "local_1")
            target_src = 1 if camera_source == "local_1" else 0
            if self.capture.config.src != target_src:
                logger.info(f"Switching local webcam source from {self.capture.config.src} to {target_src}")
                self.capture.stop()
                self.capture = VideoCaptureSkill(CaptureConfig(src=target_src)).start()
                
            frame_data = self.capture.read()
            if frame_data.grabbed and frame_data.frame is not None:
                frame = frame_data.frame.copy()
                
        if frame is None and not is_dual:
            return None

        # 2. 推理與分析階段
        inference_start = time.perf_counter()
        
        if is_dual:
            # === 雙鏡頭模式 (電腦前攝 + 手機側攝) ===
            h_l, w_l, _ = local_frame.shape
            h_p, w_p, _ = phone_frame.shape
            
            # 前鏡頭作 face_mesh, 側鏡頭作 pose
            local_rgb = cv2.cvtColor(local_frame, cv2.COLOR_BGR2RGB)
            inference_results = self.face_mesh.process(local_rgb)
            
            phone_rgb = cv2.cvtColor(phone_frame, cv2.COLOR_BGR2RGB)
            pose_results = self.pose.process(phone_rgb)
            
            inference_time_ms = int((time.perf_counter() - inference_start) * 1000)
            
            landmarks = inference_results.multi_face_landmarks[0] if (inference_results and inference_results.multi_face_landmarks) else None
            pose_landmarks = pose_results.pose_landmarks if (pose_results and pose_results.pose_landmarks) else None
            
            if landmarks:
                # 前攝特徵
                eye_dist, nc_dist = self._extract_physical_features(landmarks, w_l, h_l)
                
                # 側攝特徵 (基於 phone_frame 的維度)
                sh_width, sh_mid_x, sh_mid_y = 0.0, 0.0, 0.0
                if pose_landmarks:
                    sh_width, sh_mid_x, sh_mid_y = self._extract_shoulder_features(pose_landmarks, w_p, h_p)
                else:
                    # 虛擬肩膀備用數據 (對應 local landmarks)
                    left_eye = landmarks.landmark[33]
                    right_eye = landmarks.landmark[263]
                    face_center_x = (left_eye.x * w_l + right_eye.x * w_l) / 2.0
                    face_center_y = (left_eye.y * h_l + right_eye.y * h_l) / 2.0
                    
                    if self.is_calibrated and self.baseline_eye_distance > 0 and self.baseline_shoulder_width > 0:
                        ratio = self.baseline_shoulder_width / self.baseline_eye_distance
                        sh_width = eye_dist * ratio
                    else:
                        sh_width = eye_dist * 4.5
                    sh_mid_x = face_center_x
                    sh_mid_y = face_center_y + eye_dist * 3.0
                
                # 決策邏輯
                if not self.is_calibrated:
                    calibration_result = self.wizard.process(
                        eye_dist, nc_dist,
                        current_shoulder_width=sh_width,
                        current_shoulder_midpoint_x=sh_mid_x,
                        current_shoulder_midpoint_y=sh_mid_y
                    )
                    self.state.update_status(
                        calibrating=True,
                        calibration_progress=calibration_result.progress
                    )
                    if calibration_result.is_complete:
                        self.baseline_eye_distance = calibration_result.baseline_eye_dist
                        self.baseline_nose_chin_distance = calibration_result.baseline_nc_dist
                        self.baseline_shoulder_width = calibration_result.baseline_shoulder_width
                        self.baseline_shoulder_midpoint_x = calibration_result.baseline_shoulder_midpoint_x
                        self.baseline_shoulder_midpoint_y = calibration_result.baseline_shoulder_midpoint_y
                        self.is_calibrated = True
                        self.state.update_status(baseline_eye_dist=self.baseline_eye_distance)
                        logger.success(f"Calibration successful (Dual): Baseline NC Dist = {self.baseline_nose_chin_distance:.1f}, Shoulder Width = {self.baseline_shoulder_width:.1f}")
                else:
                    self._evaluate_posture(landmarks, pose_landmarks, (w_l, h_l), (w_p, h_p), inference_time_ms)
            else:
                self.state.update_status(latency_ms=inference_time_ms)
                
            # 繪製各分鏡的標記 (不要在子畫面畫文字)
            self._annotate_frame(local_frame, landmarks, w_l, h_l, self.state.get_status(), pose_landmarks=None, draw_text=False)
            self._annotate_frame(phone_frame, None, w_p, h_p, self.state.get_status(), pose_landmarks=pose_landmarks, draw_text=False)
            
            # 將手機畫面高度縮放至與電腦畫面一致並拼接
            new_w_p = int(w_p * (h_l / h_p))
            resized_phone = cv2.resize(phone_frame, (new_w_p, h_l))
            stitched = np.hstack((local_frame, resized_phone))
            
            # 在拼接後的畫面繪製綜合狀態文字 (Stitched 寬度 = w_l + new_w_p)
            self._annotate_frame(stitched, None, w_l + new_w_p, h_l, self.state.get_status(), pose_landmarks=None, draw_text=True)
            return stitched
            
        else:
            # === 單鏡頭模式 (傳統模式) ===
            height, width, _ = frame.shape
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            inference_results = self.face_mesh.process(image_rgb)
            pose_results = self.pose.process(image_rgb)
            inference_time_ms = int((time.perf_counter() - inference_start) * 1000)
            
            landmarks = inference_results.multi_face_landmarks[0] if (inference_results and inference_results.multi_face_landmarks) else None
            pose_landmarks = pose_results.pose_landmarks if (pose_results and pose_results.pose_landmarks) else None
            
            if landmarks:
                eye_dist, nc_dist = self._extract_physical_features(landmarks, width, height)
                sh_width, sh_mid_x, sh_mid_y = 0.0, 0.0, 0.0
                if pose_landmarks:
                    sh_width, sh_mid_x, sh_mid_y = self._extract_shoulder_features(pose_landmarks, width, height)
                
                if sh_width <= 0:
                    left_eye = landmarks.landmark[33]
                    right_eye = landmarks.landmark[263]
                    face_center_x = (left_eye.x * width + right_eye.x * width) / 2.0
                    face_center_y = (left_eye.y * height + right_eye.y * height) / 2.0
                    
                    if self.is_calibrated and self.baseline_eye_distance > 0 and self.baseline_shoulder_width > 0:
                        ratio = self.baseline_shoulder_width / self.baseline_eye_distance
                        sh_width = eye_dist * ratio
                    else:
                        sh_width = eye_dist * 4.5
                    sh_mid_x = face_center_x
                    sh_mid_y = face_center_y + eye_dist * 3.0
                    
                if not self.is_calibrated:
                    calibration_result = self.wizard.process(
                        eye_dist, nc_dist,
                        current_shoulder_width=sh_width,
                        current_shoulder_midpoint_x=sh_mid_x,
                        current_shoulder_midpoint_y=sh_mid_y
                    )
                    self.state.update_status(
                        calibrating=True,
                        calibration_progress=calibration_result.progress
                    )
                    if calibration_result.is_complete:
                        self.baseline_eye_distance = calibration_result.baseline_eye_dist
                        self.baseline_nose_chin_distance = calibration_result.baseline_nc_dist
                        self.baseline_shoulder_width = calibration_result.baseline_shoulder_width
                        self.baseline_shoulder_midpoint_x = calibration_result.baseline_shoulder_midpoint_x
                        self.baseline_shoulder_midpoint_y = calibration_result.baseline_shoulder_midpoint_y
                        self.is_calibrated = True
                        self.state.update_status(baseline_eye_dist=self.baseline_eye_distance)
                        logger.success(f"Calibration successful: Baseline NC Dist = {self.baseline_nose_chin_distance:.1f}, Shoulder Width = {self.baseline_shoulder_width:.1f}")
                else:
                    self._evaluate_posture(landmarks, pose_landmarks, (width, height), (width, height), inference_time_ms)
            else:
                self.state.update_status(latency_ms=inference_time_ms)
                
            self._annotate_frame(frame, landmarks, width, height, self.state.get_status(), pose_landmarks=pose_landmarks, draw_text=True)
            return cv2.flip(frame, 1)

    def stop(self) -> None:
        """安全停止流水線並釋放資源。"""
        logger.info("Stopping AgentPipeline workflow")
        self.capture.stop()
