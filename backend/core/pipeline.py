"""
代理流水線核心 (Agent Pipeline Core)
負責協調整合各項技能，驅動整體的影像處理、姿勢分析與數據更新。
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
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
from .event_engine import EventEngine

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
        self.is_calibrated = False
        self.baseline_eye_distance = 0.0
        self.baseline_shoulder_width = 0.0

        # 1. 初始化各項技能 (Skill Initialization)
        self.captures = {}
        self.action_engine = ActionEngine(skills_dir="skills")
        self.event_engine = EventEngine(events_dir="events")
        self.wizard = CalibrationWizardSkill()
        
        # 2. MediaPipe 模型設定
        # MediaPipe Tasks API Setup
        import os
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Face Landmarker
        face_model_path = os.path.join(base_dir, 'models', 'face_landmarker.task')
        face_base_options = python.BaseOptions(model_asset_path=face_model_path)
        face_options = vision.FaceLandmarkerOptions(
            base_options=face_base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.face_landmarker = vision.FaceLandmarker.create_from_options(face_options)
        
        # Pose Landmarker
        pose_model_path = os.path.join(base_dir, 'models', 'pose_landmarker_lite.task')
        pose_base_options = python.BaseOptions(model_asset_path=pose_model_path)
        pose_options = vision.PoseLandmarkerOptions(
            base_options=pose_base_options,
            output_segmentation_masks=False,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.pose_landmarker = vision.PoseLandmarker.create_from_options(pose_options)
        
        # Backward compatibility for drawing utils
        try:
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_pose = mp.solutions.pose
        except AttributeError:
            self.mp_drawing = None
            self.mp_drawing_styles = None
            self.mp_face_mesh = None
            self.mp_pose = None

        
        self.baseline_eye_distance = 0.0
        self.baseline_nose_chin_distance = 0.0
        self.baseline_shoulder_width = 0.0
        self.baseline_shoulder_midpoint_x = 0.0
        self.baseline_shoulder_midpoint_y = 0.0
        self.baseline_face_landmarks = None
        self.baseline_pose_landmarks = None
        self.is_calibrated = False
        self.is_down_previously = False
        self.previous_states = {}
        self.trigger_counts = {}
        
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
            "shoulder_midpoint_y": self.baseline_shoulder_midpoint_y,
            "face_landmarks": self.baseline_face_landmarks,
            "pose_landmarks": self.baseline_pose_landmarks
        }
        
        status = self.state.get_status()
        # state_history 完全通用：反映所有當前觸發中的技能狀態
        state_history = {name: val for name, val in status.active_skills.items()}
        # 向後相容性 key
        state_history.setdefault("is_bad_posture", status.is_bad_posture)
        state_history.setdefault("is_swaying", status.is_swaying)
        state_history.setdefault("is_leaning_forward", status.is_leaning_forward)
        
        # 執行動作引擎評估（完全動態，不寫死技能名稱）
        results = self.action_engine.evaluate_all(
            landmarks, pose_landmarks, face_dim, body_dim, baselines, self.state.prefs, state_history
        )
        
        # 整理 active_skills 與 metrics 字典
        active_skills = {}
        metrics = {}
        for name, data in results.items():
            active_skills[name] = bool(data[0])
            metrics[name] = float(data[1])
            
        # 提取當前特徵供複合事件引擎計算
        cur_eye_dist = 0.0
        if landmarks and face_dim[0] > 0 and face_dim[1] > 0:
            cur_eye_dist, _ = self._extract_physical_features(landmarks, face_dim[0], face_dim[1])
            
        cur_sh_width = 0.0
        if pose_landmarks and body_dim[0] > 0 and body_dim[1] > 0:
            cur_sh_width, _, _ = self._extract_shoulder_features(pose_landmarks, body_dim[0], body_dim[1])
            
        # 2. 透過 EventEngine 評估複合事件規則
        active_events = self.event_engine.evaluate(
            active_skills,
            landmarks=landmarks,
            pose_landmarks=pose_landmarks,
            baselines=baselines,
            current_eye_distance=cur_eye_dist,
            current_shoulder_width=cur_sh_width,
            face_dim=face_dim,
            body_dim=body_dim
        )
        
        # 3. 動態更新各項技能與事件的警報計數
        for name, triggered in active_skills.items():
            if name not in self.trigger_counts:
                self.trigger_counts[name] = 0
            prev = self.previous_states.get(name, False)
            if triggered and not prev:
                self.trigger_counts[name] += 1
            self.previous_states[name] = triggered
            
        for name, triggered in active_events.items():
            if name not in self.trigger_counts:
                self.trigger_counts[name] = 0
            prev = self.previous_states.get(name, False)
            if triggered and not prev:
                self.trigger_counts[name] += 1
            self.previous_states[name] = triggered
            
        # 更新共享狀態
        self.state.update_status(
            ratio=0.0, # Kept for backward compatibility but default to 0
            is_bad_posture=any(active_skills.values()),
            is_turning=False,
            down_count=0,
            latency_ms=inference_time_ms,
            calibrating=False,
            is_swaying=False,
            is_leaning_forward=False,
            sway_ratio=0.0,
            lean_ratio=0.0,
            active_skills=active_skills,
            active_events=active_events,
            metrics=metrics,
            trigger_counts=self.trigger_counts
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
        
        nose = landmarks[NOSE_INDEX]
        chin = landmarks[CHIN_INDEX]
        left_eye = landmarks[LEFT_EYE_INDEX]
        right_eye = landmarks[RIGHT_EYE_INDEX]
        
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
        left_shoulder = pose_landmarks[11]
        right_shoulder = pose_landmarks[12]
        
        ls_x, ls_y = left_shoulder.x * width, left_shoulder.y * height
        rs_x, rs_y = right_shoulder.x * width, right_shoulder.y * height
        
        sh_width = math.sqrt((ls_x - rs_x)**2 + (ls_y - rs_y)**2)
        sh_mid_x = (ls_x + rs_x) / 2.0
        sh_mid_y = (ls_y + rs_y) / 2.0
        
        return sh_width, sh_mid_x, sh_mid_y

    def _annotate_frame(self, frame: np.ndarray, landmarks: Any, width: int, height: int, status: Any, pose_landmarks: Any = None, draw_text: bool = True) -> None:
        """
        在畫面上繪製 RenUniversal 核心追蹤點（雙眼、鼻、下巴、雙肩），以及額外啟用的 Skills 追蹤點。
        """
        NOSE_INDEX, CHIN_INDEX = 1, 152
        LEFT_EYE_INDEX, RIGHT_EYE_INDEX = 33, 263
        
        # 1. 繪製 RenUniversal 基礎面部追蹤點 (雙眼、鼻子、下巴)
        if landmarks is not None:
            points = [
                (landmarks[NOSE_INDEX], (255, 100, 0), "Nose"),      # 藍色 (BGR)
                (landmarks[CHIN_INDEX], (0, 0, 255), "Chin"),        # 紅色
                (landmarks[LEFT_EYE_INDEX], (0, 255, 0), "L-Eye"),    # 綠色
                (landmarks[RIGHT_EYE_INDEX], (0, 255, 0), "R-Eye")    # 綠色
            ]
            for lm, color, label in points:
                cx, cy = int(lm.x * width), int(lm.y * height)
                cv2.circle(frame, (cx, cy), 5, color, -1)
                cv2.circle(frame, (cx, cy), 7, (255, 255, 255), 1)

            # 繪製鼻尖到下巴的連線 (RenUniversal 核心：下巴內收參考線)
            nose = landmarks[NOSE_INDEX]
            chin = landmarks[CHIN_INDEX]
            cv2.line(frame, 
                     (int(nose.x * width), int(nose.y * height)), 
                     (int(chin.x * width), int(chin.y * height)), 
                     (255, 255, 255), 1, cv2.LINE_AA)

        # 2. 繪製 RenUniversal 基礎身體追蹤點 (雙肩)
        if pose_landmarks:
            left_shoulder = pose_landmarks[11]
            right_shoulder = pose_landmarks[12]
            
            ls_x, ls_y = int(left_shoulder.x * width), int(left_shoulder.y * height)
            rs_x, rs_y = int(right_shoulder.x * width), int(right_shoulder.y * height)
            
            # 判斷顏色：若有任何肩膀不良姿勢（搖晃或前傾），顯示紅色，否則顯示綠色
            sh_color = (0, 0, 255) if (getattr(status, 'is_swaying', False) or getattr(status, 'is_leaning_forward', False)) else (0, 255, 0)
            
            cv2.circle(frame, (ls_x, ls_y), 6, sh_color, -1)
            cv2.circle(frame, (rs_x, rs_y), 6, sh_color, -1)
            cv2.circle(frame, (ls_x, ls_y), 8, (255, 255, 255), 1)
            cv2.circle(frame, (rs_x, rs_y), 8, (255, 255, 255), 1)
            cv2.line(frame, (ls_x, ls_y), (rs_x, rs_y), sh_color, 2, cv2.LINE_AA)

        # 3. 收集並繪製「非預設」的自訂 Skills 點位
        active_points = set()
        for detector in self.action_engine.detectors.values():
            if hasattr(detector, "get_used_points"):
                active_points.update(detector.get_used_points())
                
        default_pts = {'f1', 'f152', 'f33', 'f263', 'p11', 'p12'}
        custom_points = active_points - default_pts
        
        for pt_id in custom_points:
            try:
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
                    v = int(pt_id)
                    is_pose = (v <= 32)
                    idx_str = str(v)
                
                idx = int(idx_str)
                lm = None
                if is_pose and pose_landmarks:
                    if isinstance(pose_landmarks, list) and idx < len(pose_landmarks):
                        lm = pose_landmarks[idx]
                    elif hasattr(pose_landmarks, 'landmark') and idx < len(pose_landmarks.landmark):
                        lm = pose_landmarks.landmark[idx]
                elif not is_pose and landmarks:
                    if isinstance(landmarks, list) and idx < len(landmarks):
                        lm = landmarks[idx]
                    elif hasattr(landmarks, 'landmark') and idx < len(landmarks.landmark):
                        lm = landmarks.landmark[idx]
                
                if lm is None:
                    continue
                    
                cx, cy = int(lm.x * width), int(lm.y * height)
                # 自訂點位使用紫色/粉紅色顯示以區分
                cv2.circle(frame, (cx, cy), 5, (255, 0, 255), -1)
                cv2.circle(frame, (cx, cy), 7, (255, 255, 255), 1)
            except Exception:
                pass

        # 4. 繪製自訂 Skills 的點位連線
        active_pairs = []
        for name, detector in self.action_engine.detectors.items():
            if hasattr(detector, "get_point_pairs"):
                triggered = getattr(status, 'active_skills', {}).get(name, False)
                for p1, p2 in detector.get_point_pairs():
                    active_pairs.append((p1, p2, triggered))

        for p1_id, p2_id, triggered in active_pairs:
            try:
                def get_pt(pt_id):
                    pt_id = str(pt_id).strip().lower()
                    if pt_id.startswith('p'):
                        idx = int(pt_id[1:])
                        if pose_landmarks and isinstance(pose_landmarks, list) and idx < len(pose_landmarks):
                            return pose_landmarks[idx]
                        elif pose_landmarks and hasattr(pose_landmarks, 'landmark') and idx < len(pose_landmarks.landmark):
                            return pose_landmarks.landmark[idx]
                    elif pt_id.startswith('f'):
                        idx = int(pt_id[1:])
                        if landmarks and isinstance(landmarks, list) and idx < len(landmarks):
                            return landmarks[idx]
                        elif landmarks and hasattr(landmarks, 'landmark') and idx < len(landmarks.landmark):
                            return landmarks.landmark[idx]
                    else:
                        idx = int(pt_id)
                        if idx <= 32 and pose_landmarks:
                            if isinstance(pose_landmarks, list) and idx < len(pose_landmarks):
                                return pose_landmarks[idx]
                            elif hasattr(pose_landmarks, 'landmark') and idx < len(pose_landmarks.landmark):
                                return pose_landmarks.landmark[idx]
                    return None

                lm1 = get_pt(p1_id)
                lm2 = get_pt(p2_id)
                if lm1 and lm2:
                    cx1, cy1 = int(lm1.x * width), int(lm1.y * height)
                    cx2, cy2 = int(lm2.x * width), int(lm2.y * height)
                    
                    # 預設藍色，觸發變紅 (BGR 格式)
                    color = (0, 0, 255) if triggered else (255, 100, 0)
                    cv2.line(frame, (cx1, cy1), (cx2, cy2), color, 2, cv2.LINE_AA)
            except Exception:
                pass

        # 3. 繪製狀態文字 (如果啟用)
        if draw_text:
            status_text = "CALIBRATING..." if status.calibrating else "SYSTEM RUNNING"
            color = (0, 255, 0) if not status.calibrating else (255, 255, 255)
            
            # 陰影文字增加可讀性
            display_y = 40
            cv2.putText(frame, status_text, (20, display_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, status_text, (20, display_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1, cv2.LINE_AA)
            
            # 顯示延遲與計數及肩膀比例
            info_parts = [f"Lat: {status.latency_ms}ms"]
            if not status.calibrating:
                for name, val in status.metrics.items():
                    info_parts.append(f"{name}: {val:.2f}")
            info_text = " | ".join(info_parts[:5]) # 限制最多顯示 5 個防爆
            
            cv2.putText(frame, info_text, (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, info_text, (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

            if status.calibrating:
                progress_bar_w = int(width * 0.6 * status.calibration_progress / 100)
                cv2.rectangle(frame, (20, 60), (20 + int(width * 0.6), 75), (50, 50, 50), -1)
                cv2.rectangle(frame, (20, 60), (20 + progress_bar_w, 75), (0, 255, 0), -1)

    def run_cycle(self) -> Optional[np.ndarray]:
        """
        執行一次流水線循環：抓取影格 -> 辨識特徵 -> 校準/動作檢測 -> 事件評估 -> 回傳可視化影格。
        """
        status = self.state.get_status()
        camera_sources = getattr(status, "camera_source", ["local_0"])
        
        # Ensure it's a list
        if isinstance(camera_sources, str):
            if camera_sources == "dual": camera_sources = ["local_0", "phone"]
            else: camera_sources = [camera_sources]
            
        if not camera_sources:
            return None
            
        # 1. 擷取所有鏡頭畫面
        frames = [] # list of (src_name, frame)
        
        for src in camera_sources:
            if src == "phone":
                net_frame, last_time = self.state.get_network_frame()
                import time as t_mod
                if net_frame is not None and (t_mod.time() - last_time) < 3.0:
                    frames.append((src, net_frame.copy()))
            elif src.startswith("local_"):
                try: idx = int(src.split("_")[1])
                except: idx = 0
                
                # Check if we need to start it
                if src not in self.captures:
                    from backend.services.video_capture.logic import VideoCaptureSkill
                    from backend.services.video_capture.schema import CaptureConfig
                    logger.info(f"Starting local webcam {src}")
                    self.captures[src] = VideoCaptureSkill(CaptureConfig(src=idx)).start()
                
                frame_data = self.captures[src].read()
                if frame_data.grabbed and frame_data.frame is not None:
                    # flip if it's local and flip_enabled
                    f = frame_data.frame.copy()
                    if status.flip_enabled:
                        f = cv2.flip(f, 1)
                    frames.append((src, f))
                    
        # 清理不再使用的 local cameras
        active_locals = [s for s in camera_sources if s.startswith("local_")]
        to_remove = [s for s in self.captures if s not in active_locals]
        for s in to_remove:
            logger.info(f"Stopping unused camera {s}")
            self.captures[s].stop()
            del self.captures[s]
            
        if not frames:
            return None
            
        if not status.is_active:
            # 暫停模式：直接回傳拼接後的畫面，不跑 AI
            return self._stitch_frames(frames)

        # 2. 推理與分析：強制搜尋所有鏡頭，尋找臉部與身體
        inference_start = time.perf_counter()
        
        frames_rgb = [(src, frame, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)) for src, frame in frames]
        
        landmarks = None
        face_frame_tuple = frames[0]
        for src, frame, rgb in frames_rgb:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            res = self.face_landmarker.detect(mp_image)
            if res and res.face_landmarks and len(res.face_landmarks) > 0:
                landmarks = res.face_landmarks[0]
                face_frame_tuple = (src, frame)
                break
                
        pose_landmarks = None
        pose_frame_tuple = frames[0]
        for src, frame, rgb in frames_rgb:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            res = self.pose_landmarker.detect(mp_image)
            if res and res.pose_landmarks and len(res.pose_landmarks) > 0:
                pose_landmarks = res.pose_landmarks[0]
                pose_frame_tuple = (src, frame)
                break
            
        inference_time_ms = int((time.perf_counter() - inference_start) * 1000)
        
        # 進行動作引擎分析 (綁定到 face_frame_tuple 畫面上，因為特徵大多在臉部)
        h_f, w_f, _ = face_frame_tuple[1].shape
        active_skills_state = {}
        metrics_state = {}
        
        if landmarks:
            eye_dist, nc_dist = self._extract_physical_features(landmarks, w_f, h_f)
            sh_width = 0.0
            sh_mid_x = 0.0
            sh_mid_y = 0.0
            if pose_landmarks:
                sh_width, sh_mid_x, sh_mid_y = self._extract_shoulder_features(pose_landmarks, w_f, h_f)
                
            if status.calibrating:
                # 校準中
                
                # Check for old API vs Tasks API
                if isinstance(landmarks, list):
                    face_dict = [{"x": l.x, "y": l.y} for l in landmarks]
                else:
                    face_dict = [{"x": l.x, "y": l.y} for l in landmarks.landmark]
                    
                if pose_landmarks:
                    if isinstance(pose_landmarks, list):
                        pose_dict = [{"x": l.x, "y": l.y} for l in pose_landmarks]
                    else:
                        pose_dict = [{"x": l.x, "y": l.y} for l in pose_landmarks.landmark]
                else:
                    pose_dict = None
                wizard_status = self.wizard.process(
                    eye_dist, nc_dist,
                    current_shoulder_width=sh_width,
                    current_shoulder_midpoint_x=sh_mid_x,
                    current_shoulder_midpoint_y=sh_mid_y,
                    face_landmarks=face_dict,
                    pose_landmarks=pose_dict
                )
                self.state.update_status(
                    calibration_progress=wizard_status.progress,
                    calibrating=not wizard_status.is_complete,
                    baseline_eye_dist=wizard_status.baseline_eye_dist if wizard_status.is_complete else status.baseline_eye_dist
                )
                if wizard_status.is_complete:
                    self.is_calibrated = True
                    self.baseline_eye_distance = wizard_status.baseline_eye_dist
                    self.baseline_nose_chin_distance = wizard_status.baseline_nc_dist
                    self.baseline_shoulder_width = wizard_status.baseline_shoulder_width
                    self.baseline_shoulder_midpoint_x = wizard_status.baseline_shoulder_midpoint_x
                    self.baseline_shoulder_midpoint_y = wizard_status.baseline_shoulder_midpoint_y
                    self.baseline_face_landmarks = wizard_status.baseline_face_landmarks
                    self.baseline_pose_landmarks = wizard_status.baseline_pose_landmarks
                    self.state.save_prefs({
                        "last_baseline_eye": wizard_status.baseline_eye_dist,
                        "username": "User"
                    })
                
                if landmarks and self.mp_drawing and self.mp_drawing_styles and self.mp_face_mesh:
                    self.mp_drawing.draw_landmarks(
                        image=face_frame_tuple[1],
                        landmark_list=landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                    )
            else:
                # 動作分析 — 使用正確的 evaluate_all() 介面
                baselines_for_eval = {
                    "eye_distance": self.baseline_eye_distance,
                    "nose_chin_distance": self.baseline_nose_chin_distance,
                    "shoulder_width": self.baseline_shoulder_width,
                    "shoulder_midpoint_x": self.baseline_shoulder_midpoint_x,
                    "shoulder_midpoint_y": self.baseline_shoulder_midpoint_y,
                    "face_landmarks": self.baseline_face_landmarks,
                    "pose_landmarks": self.baseline_pose_landmarks,
                    "_current_eye_distance": eye_dist,
                    "_current_shoulder_width": sh_width,
                }
                state_history = {name: val for name, val in status.active_skills.items()}

                results = self.action_engine.evaluate_all(
                    landmarks,
                    pose_landmarks,
                    face_dim=(w_f, h_f),
                    body_dim=(w_f, h_f),
                    baselines=baselines_for_eval,
                    preferences=self.state.prefs,
                    state_history=state_history
                )

                # 整理結果 — evaluate_all 回傳 {name: (is_triggered, metric_val, debug_info)}
                for name, (is_triggered, metric_val, debug_info) in results.items():
                    active_skills_state[name] = bool(is_triggered)
                    metrics_state[name] = float(metric_val)

                # --- 繪製可視化 (Visualization) ---
                # 不再繪製整張網格，而是繪製已啟用技能的連線與點位
                active_pairs = []
                for name, detector in self.action_engine.detectors.items():
                    if name in active_skills_state:
                        triggered = active_skills_state[name]
                        if hasattr(detector, 'get_point_pairs'):
                            for p1, p2 in detector.get_point_pairs():
                                active_pairs.append((p1, p2, triggered))

                for p1_id, p2_id, triggered in active_pairs:
                    try:
                        def get_pt(pt_id):
                            pt_id = str(pt_id).strip().lower()
                            if pt_id.startswith('p'):
                                idx = int(pt_id[1:])
                                if pose_landmarks:
                                    if isinstance(pose_landmarks, list) and idx < len(pose_landmarks):
                                        return pose_landmarks[idx]
                                    elif hasattr(pose_landmarks, 'landmark') and idx < len(pose_landmarks.landmark):
                                        return pose_landmarks.landmark[idx]
                            elif pt_id.startswith('f'):
                                idx = int(pt_id[1:])
                                if landmarks:
                                    if isinstance(landmarks, list) and idx < len(landmarks):
                                        return landmarks[idx]
                                    elif hasattr(landmarks, 'landmark') and idx < len(landmarks.landmark):
                                        return landmarks.landmark[idx]
                            else:
                                idx = int(pt_id)
                                if idx <= 32 and pose_landmarks:
                                    if isinstance(pose_landmarks, list) and idx < len(pose_landmarks):
                                        return pose_landmarks[idx]
                                    elif hasattr(pose_landmarks, 'landmark') and idx < len(pose_landmarks.landmark):
                                        return pose_landmarks.landmark[idx]
                            return None

                        lm1 = get_pt(p1_id)
                        lm2 = get_pt(p2_id)
                        if lm1 and lm2:
                            # 判斷這個點應該畫在哪個 frame (單相機就都在 face_frame_tuple[1], 雙相機的話 pose 點在 pose frame)
                            def is_pose_id(pid):
                                pid = str(pid).strip().lower()
                                return pid.startswith('p') or (pid.isdigit() and int(pid) <= 32)

                            target_frame_1 = pose_frame_tuple[1] if (is_pose_id(p1_id) and face_frame_tuple[0] != pose_frame_tuple[0]) else face_frame_tuple[1]
                            target_frame_2 = pose_frame_tuple[1] if (is_pose_id(p2_id) and face_frame_tuple[0] != pose_frame_tuple[0]) else face_frame_tuple[1]
                            
                            h1, w1, _ = target_frame_1.shape
                            h2, w2, _ = target_frame_2.shape
                            
                            cx1, cy1 = int(lm1.x * w1), int(lm1.y * h1)
                            cx2, cy2 = int(lm2.x * w2), int(lm2.y * h2)
                            
                            color = (0, 0, 255) if triggered else (0, 255, 0) # BGR 格式 (紅:觸發, 綠:監控)
                            
                            # 如果兩個點在同一個 frame 上，才畫線，否則只畫點
                            if target_frame_1 is target_frame_2:
                                cv2.line(target_frame_1, (cx1, cy1), (cx2, cy2), color, 2, cv2.LINE_AA)
                                
                            cv2.circle(target_frame_1, (cx1, cy1), 4, color, -1)
                            cv2.circle(target_frame_2, (cx2, cy2), 4, color, -1)
                    except Exception as e:
                        pass

        # 4.5 繪製虛擬膠囊 (Virtual Capsules for debugging)
        for name, detector in self.action_engine.detectors.items():
            if hasattr(detector, 'capsules_to_draw'):
                for cap in detector.capsules_to_draw:
                    b1 = cap["b1"]
                    b2 = cap["b2"]
                    if not b1 or not b2:
                        continue
                    r = int(cap["radius"])
                    triggered = cap["triggered"]
                    pt1_id = cap["pt1_id"]
                    
                    def is_pose_id(pid):
                        pid = str(pid).strip().lower()
                        return pid.startswith('p') or (pid.isdigit() and int(pid) <= 32)
                        
                    target_frame = pose_frame_tuple[1] if (is_pose_id(pt1_id) and face_frame_tuple[0] != pose_frame_tuple[0]) else face_frame_tuple[1]
                    
                    # 黃色表示膠囊區，紅色表示出界觸發
                    color = (0, 0, 255) if triggered else (0, 255, 255)
                    
                    cx1, cy1 = int(b1[0]), int(b1[1])
                    cx2, cy2 = int(b2[0]), int(b2[1])
                    
                    cv2.circle(target_frame, (cx1, cy1), r, color, 1, cv2.LINE_AA)
                    cv2.circle(target_frame, (cx2, cy2), r, color, 1, cv2.LINE_AA)
                    
                    vx = cx2 - cx1
                    vy = cy2 - cy1
                    length = math.sqrt(vx*vx + vy*vy)
                    if length > 0:
                        nx = -vy / length
                        ny = vx / length
                        ox = int(nx * r)
                        oy = int(ny * r)
                        
                        cv2.line(target_frame, (cx1 + ox, cy1 + oy), (cx2 + ox, cy2 + oy), color, 1, cv2.LINE_AA)
                        cv2.line(target_frame, (cx1 - ox, cy1 - oy), (cx2 - ox, cy2 - oy), color, 1, cv2.LINE_AA)



        # 3. 事件引擎評估 (Event Engine)
        _baselines = {
            "eye_distance": self.baseline_eye_distance,
            "nose_chin_distance": self.baseline_nose_chin_distance,
            "shoulder_width": self.baseline_shoulder_width,
            "face_landmarks": self.baseline_face_landmarks,
            "pose_landmarks": self.baseline_pose_landmarks,
        }
        active_events_state = self.event_engine.evaluate(
            active_skills_dict=active_skills_state,
            landmarks=landmarks,
            pose_landmarks=pose_landmarks,
            baselines=_baselines,
            current_eye_distance=metrics_state.get("eye_distance", 0.0),
            current_shoulder_width=metrics_state.get("shoulder_width", 0.0),
            face_dim=(w_f, h_f) if landmarks else (640, 480),
            body_dim=(w_f, h_f) if pose_landmarks else (640, 480)
        )
        
        # 4. 同步狀態與觸發統計 (Metrics & State Sync)
        for name, triggered in active_skills_state.items():
            if name not in self.trigger_counts:
                self.trigger_counts[name] = 0
            prev = self.previous_states.get(name, False)
            if triggered and not prev:
                self.trigger_counts[name] += 1
            self.previous_states[name] = triggered
            
        for name, triggered in active_events_state.items():
            if name not in self.trigger_counts:
                self.trigger_counts[name] = 0
            prev = self.previous_states.get(name, False)
            if triggered and not prev:
                self.trigger_counts[name] += 1
            self.previous_states[name] = triggered

        self.state.update_status(
            latency_ms=inference_time_ms,
            active_skills=active_skills_state,
            active_events=active_events_state,
            metrics=metrics_state,
            trigger_counts=self.trigger_counts
        )

        # 5. 多畫面合併 (Stitching)
        return self._stitch_frames(frames)
        
    def _stitch_frames(self, frames: list) -> np.ndarray:
        """將多個影格縫合成單一畫面 (Grid Layout)"""
        if len(frames) == 1:
            return frames[0][1]
            
        # 將所有畫面縮放到相同高度 (以第一格為準)
        base_h = 480
        processed_frames = []
        for src, f in frames:
            h, w = f.shape[:2]
            scale = base_h / h
            new_w = int(w * scale)
            resized = cv2.resize(f, (new_w, base_h))
            # 加上相機標籤
            cv2.putText(resized, src, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            processed_frames.append(resized)
            
        if len(processed_frames) == 2:
            return cv2.hconcat(processed_frames)
        elif len(processed_frames) <= 4:
            # 2x2 grid
            while len(processed_frames) < 4:
                processed_frames.append(np.zeros_like(processed_frames[0]))
            top = cv2.hconcat([processed_frames[0], processed_frames[1]])
            bottom = cv2.hconcat([processed_frames[2], processed_frames[3]])
            return cv2.vconcat([top, bottom])
        else:
            # 3x2 grid
            while len(processed_frames) < 6:
                processed_frames.append(np.zeros_like(processed_frames[0]))
            top = cv2.hconcat([processed_frames[0], processed_frames[1], processed_frames[2]])
            bottom = cv2.hconcat([processed_frames[3], processed_frames[4], processed_frames[5]])
            return cv2.vconcat([top, bottom])

    def stop(self):
        """停止所有相機並釋放資源。"""
        logger.info("Stopping AgentPipeline workflow")
        for src, cap in self.captures.items():
            logger.info(f"Stopping camera {src}")
            cap.stop()
        self.captures.clear()
