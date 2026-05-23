import re

with open('backend/services/video_capture/logic.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_stop = """    def stop(self) -> None:
        \"\"\"停止捕捉並同步釋放硬體資源。\"\"\"
        logger.info(f"Stopping VideoCaptureSkill on source {self.config.src}")
        self.stopped = True
        
        # 等待執行緒結束
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            
        with self.lock:
            if hasattr(self, 'stream') and self.stream.isOpened():
                self.stream.release()
"""

# replace the stop method
pattern = r"    def stop\(self\) -> None:.*?logger\.info\(f\"Stopping VideoCaptureSkill on source \{self\.config\.src\}\"\).*?self\.stopped = True"

content = re.sub(pattern, new_stop.strip(), content, flags=re.DOTALL)

# we also need to save the thread object in start()
start_pattern = r"t = threading\.Thread\(target=self\._capture_worker, args=\(\), daemon=True\)\n\s*t\.start\(\)"
new_start = "self.thread = threading.Thread(target=self._capture_worker, args=(), daemon=True)\n        self.thread.start()"
content = re.sub(start_pattern, new_start, content)

with open('backend/services/video_capture/logic.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched VideoCaptureSkill to synchronously release camera")
