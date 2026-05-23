import re

with open('backend/core/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We want to add an if-check after getting the frames
old_code = r"""        if not frames:
            return None

        # 決定誰跑 AI"""

new_code = r"""        if not frames:
            return None
            
        if not status.is_active:
            # 暫停模式：直接回傳拼接後的畫面，不跑 AI
            stitched = self._stitch_frames(frames)
            import cv2
            return cv2.addWeighted(stitched, 0.5, stitched, 0, 0)

        # 決定誰跑 AI"""

content = re.sub(old_code, new_code, content)

with open('backend/core/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated pipeline for paused mode")
