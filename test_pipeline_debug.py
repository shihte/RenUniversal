import re

with open('backend/core/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add logging
old_code = r"""                frame_data = self.captures\[src\]\.read\(\)
                if frame_data.grabbed and frame_data.frame is not None:"""
new_code = r"""                frame_data = self.captures[src].read()
                if not frame_data.grabbed:
                    logger.warning(f"Frame not grabbed for {src}")
                elif frame_data.frame is None:
                    logger.warning(f"Frame is None for {src}")
                
                if frame_data.grabbed and frame_data.frame is not None:"""

content = re.sub(old_code, new_code, content)

with open('backend/core/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added debug logging to pipeline.py")
