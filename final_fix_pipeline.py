import re

with open('backend/core/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix UnboundLocalError
content = content.replace("import cv2\n            return cv2.addWeighted(", "# no import cv2 here\n            return cv2.addWeighted(")

# Fix event engine evaluate argument and return value
# Search for:
#        event_ctx = {
#            "skills": active_skills_state,
#            "metrics": metrics_state,
#            "calibrating": status.calibrating
#        }
#        event_results = self.event_engine.evaluate(event_ctx)
#        
#        # 整理事件觸發狀態
#        active_events_state = {evt.event_id: evt.is_triggered for evt in event_results}

old_event_code = r"""        # 3. 事件引擎評估 \(Event Engine\)
        event_ctx = \{
            "skills": active_skills_state,
            "metrics": metrics_state,
            "calibrating": status\.calibrating
        \}
        event_results = self\.event_engine\.evaluate\(event_ctx\)
        
        # 整理事件觸發狀態
        active_events_state = \{evt\.event_id: evt\.is_triggered for evt in event_results\}"""

new_event_code = """        # 3. 事件引擎評估 (Event Engine)
        active_events_state = self.event_engine.evaluate(
            active_skills_dict=active_skills_state,
            landmarks=face_landmarks,
            pose_landmarks=pose_landmarks,
            baselines=self.state.get_status()._baseline_distances if hasattr(self.state.get_status(), '_baseline_distances') else None,
            current_eye_distance=metrics_state.get("eye_distance", 0.0),
            current_shoulder_width=metrics_state.get("shoulder_width", 0.0),
            face_dim=(w, h) if 'w' in locals() else (640, 480),
            body_dim=(w, h) if 'w' in locals() else (640, 480)
        )"""

content = re.sub(old_event_code, new_event_code, content)

with open('backend/core/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed event engine call and cv2 unbound error")
