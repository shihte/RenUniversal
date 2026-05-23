import re

with open('backend/services/video_capture/logic.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("self.backend = cv2.CAP_ANY", "self.backend = cv2.CAP_AVFOUNDATION if platform.system() == 'Darwin' else cv2.CAP_ANY")

with open('backend/services/video_capture/logic.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Restored CAP_AVFOUNDATION")
