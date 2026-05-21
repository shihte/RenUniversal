import re

with open('backend/services/video_capture/logic.py', 'r') as f:
    code = f.read()

# Replace cv2.VideoCapture(config.src) with cv2.VideoCapture(config.src, cv2.CAP_AVFOUNDATION) if on mac
# Actually let's just do it dynamically:
replacement = """import platform
        backend = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" else cv2.CAP_ANY
        self.stream = cv2.VideoCapture(config.src, backend)"""

code = re.sub(r'self\.stream = cv2\.VideoCapture\(config\.src\)', replacement, code)
code = re.sub(r'self\.stream = cv2\.VideoCapture\(self\.config\.src\)', 'self.stream = cv2.VideoCapture(self.config.src, backend)', code)

with open('backend/services/video_capture/logic.py', 'w') as f:
    f.write(code)
