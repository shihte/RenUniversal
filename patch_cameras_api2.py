import re

with open('backend/stream_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add a /cameras API
api_code = r"""
@app.route('/cameras')
def get_cameras():
    import subprocess
    import platform
    from flask import jsonify
    cameras = ["local_0"] # always assume at least 1 internal
    try:
        if platform.system() == "Darwin":
            out = subprocess.check_output(["system_profiler", "SPCameraDataType"], text=True)
            count = out.count("Model ID:")
            if count > 1:
                for i in range(1, count):
                    cameras.append(f"local_{i}")
    except Exception:
        pass
    cameras.append("phone")
    return jsonify({"cameras": cameras})
"""

# Find a good place to insert it
content = content.replace("@app.route('/status')", api_code + "\n@app.route('/status')")

with open('backend/stream_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully added /cameras endpoint")
