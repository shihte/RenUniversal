import re

with open('backend/stream_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_logic = """
            if state.get_status().is_active:
                processed_frame = pipeline.run_cycle()
                if processed_frame is not None:
                    state.update_frame(processed_frame)
            else:
                # 暫停模式：僅讀取影格但不處理分析 (尊重當前選擇的鏡頭)
                cam_source = state.get_status().camera_source
                dimmed = None
                
                if cam_source == "phone":
                    net_frame, last_time = state.get_network_frame()
                    import time as t_mod
                    if net_frame is not None and (t_mod.time() - last_time) < 3.0:
                        dimmed = cv2.addWeighted(net_frame, 0.5, net_frame, 0, 0)
                
                if dimmed is None:
                    frame_data = pipeline.capture.read()
                    if frame_data.frame is not None:
                        import cv2
                        dimmed = cv2.addWeighted(frame_data.frame, 0.5, frame_data.frame, 0, 0)
                
                if dimmed is not None:
                    state.update_frame(dimmed)
"""

pattern = r"if state\.get_status\(\)\.is_active:.*?state\.update_frame\(dimmed\)"
content = re.sub(pattern, new_logic.strip(), content, flags=re.DOTALL)

with open('backend/stream_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched capture loop to respect camera source when paused")
