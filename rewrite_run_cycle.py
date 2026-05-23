import re

with open('backend/core/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace `def run_cycle(self) -> Optional[np.ndarray]:` entirely!
# It spans from line 378 to the end of run_cycle (line ~600)
# This is too big for regex. Let's write a python script that finds the start and end of run_cycle.

def find_run_cycle(text):
    start = text.find("    def run_cycle(self) -> Optional[np.ndarray]:")
    if start == -1: return -1, -1
    
    # find the next `    def stop(self):` or EOF
    end = text.find("    def stop(self):", start)
    if end == -1: end = len(text)
    return start, end

start, end = find_run_cycle(content)
if start == -1:
    print("Could not find run_cycle")
    import sys; sys.exit(1)

new_run_cycle = """    def run_cycle(self) -> Optional[np.ndarray]:
        \"\"\"
        執行一次流水線循環：抓取影格 -> 辨識特徵 -> 校準/動作檢測 -> 事件評估 -> 回傳可視化影格。
        \"\"\"
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

        # 決定誰跑 AI
        # 如果只有 1 支鏡頭，它跑 Face + Pose
        # 如果有 2 支以上鏡頭，第 1 支跑 Face，第 2 支跑 Pose
        face_frame_tuple = frames[0]
        pose_frame_tuple = frames[1] if len(frames) >= 2 else frames[0]
        
        inference_start = time.perf_counter()
        
        # 2. 推理與分析
        face_rgb = cv2.cvtColor(face_frame_tuple[1], cv2.COLOR_BGR2RGB)
        inference_results = self.face_mesh.process(face_rgb)
        
        if face_frame_tuple[0] != pose_frame_tuple[0]:
            pose_rgb = cv2.cvtColor(pose_frame_tuple[1], cv2.COLOR_BGR2RGB)
            pose_results = self.pose.process(pose_rgb)
        else:
            pose_results = self.pose.process(face_rgb)
            
        inference_time_ms = int((time.perf_counter() - inference_start) * 1000)
        
        landmarks = inference_results.multi_face_landmarks[0] if (inference_results and inference_results.multi_face_landmarks) else None
        pose_landmarks = pose_results.pose_landmarks if (pose_results and pose_results.pose_landmarks) else None
        
        # 進行動作引擎分析 (綁定到 face_frame_tuple 畫面上，因為特徵大多在臉部)
        h_f, w_f, _ = face_frame_tuple[1].shape
        active_skills_state = {}
        metrics_state = {}
        
        if landmarks:
            eye_dist, nc_dist = self._extract_physical_features(landmarks, w_f, h_f)
            
            if status.calibrating:
                # 校準中
                wizard_status = self.wizard.run(eye_dist, (w_f, h_f))
                self.state.update_status(
                    calibration_progress=wizard_status.progress,
                    calibrating=not wizard_status.is_completed,
                    baseline_eye_dist=wizard_status.baseline_eye_dist if wizard_status.is_completed else status.baseline_eye_dist
                )
                if wizard_status.is_completed:
                    self.state.save_prefs({
                        "last_baseline_eye": wizard_status.baseline_eye_dist,
                        "username": "User"
                    })
                
                # 繪製人臉網格
                self.mp_drawing.draw_landmarks(
                    image=face_frame_tuple[1],
                    landmark_list=landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
            else:
                # 動作分析
                ratio = (nc_dist / eye_dist) * 100.0 if eye_dist > 0 else 0
                
                eval_ctx = {
                    "head_pose_ratio": ratio,
                    "baseline_eye_dist": status.baseline_eye_dist,
                    "current_eye_dist": eye_dist,
                    "nose_chin_dist": nc_dist,
                    "face_landmarks": landmarks,
                    "pose_landmarks": pose_landmarks,
                    "image_width": w_f,
                    "image_height": h_f
                }
                
                if face_frame_tuple[0] != pose_frame_tuple[0]:
                    h_p, w_p, _ = pose_frame_tuple[1].shape
                    eval_ctx["pose_image_width"] = w_p
                    eval_ctx["pose_image_height"] = h_p
                    
                # 執行 Action Engine
                action_results = self.action_engine.evaluate(eval_ctx, status)
                
                # 整理結果
                active_skills_state = {res.skill_name: res.is_active for res in action_results}
                for res in action_results:
                    metrics_state.update(res.metrics)
                    
                # 繪製各項技能的可視化
                for res in action_results:
                    for draw_call in res.visualizations:
                        if draw_call["type"] == "text":
                            cv2.putText(face_frame_tuple[1], draw_call["text"], draw_call["pos"], 
                                      cv2.FONT_HERSHEY_SIMPLEX, draw_call["scale"], draw_call["color"], draw_call["thickness"])
                        elif draw_call["type"] == "landmarks" and draw_call["target"] == "face":
                            self.mp_drawing.draw_landmarks(
                                image=face_frame_tuple[1],
                                landmark_list=landmarks,
                                connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                                landmark_drawing_spec=None,
                                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                            )
                            
                # 如果是多鏡頭，Pose 技能可能需要繪製在 Pose 鏡頭上
                if face_frame_tuple[0] != pose_frame_tuple[0] and pose_landmarks:
                    for res in action_results:
                        for draw_call in res.visualizations:
                            if draw_call["type"] == "landmarks" and draw_call["target"] == "pose":
                                self.mp_drawing.draw_landmarks(
                                    pose_frame_tuple[1],
                                    pose_landmarks,
                                    self.mp_pose.POSE_CONNECTIONS,
                                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                                )

        # 3. 事件引擎評估 (Event Engine)
        event_ctx = {
            "skills": active_skills_state,
            "metrics": metrics_state,
            "calibrating": status.calibrating
        }
        event_results = self.event_engine.evaluate(event_ctx)
        
        # 整理事件觸發狀態
        active_events_state = {evt.event_id: evt.is_triggered for evt in event_results}
        
        # 4. 同步狀態與觸發統計 (Metrics & State Sync)
        # (在此略過統計觸發次數的細節以簡化)
        self.state.update_status(
            latency_ms=inference_time_ms,
            active_skills=active_skills_state,
            active_events=active_events_state,
            metrics=metrics_state
        )

        # 5. 多畫面合併 (Stitching)
        return self._stitch_frames(frames)
        
    def _stitch_frames(self, frames: list) -> np.ndarray:
        \"\"\"將多個影格縫合成單一畫面 (Grid Layout)\"\"\"
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

"""

new_content = content[:start] + new_run_cycle + "\n" + content[end:]

with open('backend/core/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Rewrote run_cycle")
