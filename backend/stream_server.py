import os
import time
import argparse
import threading
import socket
import subprocess
import re
import json
from flask import Flask, Response, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
import cv2
from loguru import logger
from pydantic import ValidationError

from core import SharedState
from core.pipeline import AgentPipeline
from core.schema import SettingsUpdate, ControlCommand

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def start_tunnel(port=8080):
    """
    啟動內網穿透服務 (localhost.run)，將本地服務曝露至公網，以便手機在不同網路環境下連線。
    """
    def run():
        cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "-R", f"80:localhost:{port}", "nokey@localhost.run"]
        logger.info("Initializing intranet tunnel via localhost.run...")
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                match = re.search(r'https://[a-zA-Z0-9-.]+\.lhr\.life', line)
                if match:
                    public_url = match.group(0)
                    logger.success(f"Intranet Tunnel established successfully!")
                    logger.success(f"Public Link: {public_url}")
                    logger.success(f"Mobile Public Link: {public_url}/mobile")
                    state.update_status(public_url=public_url)
        except Exception as e:
            logger.error(f"Failed to start intranet tunnel: {e}")

    threading.Thread(target=run, daemon=True).start()

# 路徑定義
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
WEB_DIR = os.path.join(PROJECT_ROOT, 'web')

app = Flask(__name__, template_folder=WEB_DIR)
CORS(app)

# 初始化共享狀態 (具備 Memory 功能)
state = SharedState()


# 全局代理流水線
service_context = {
    "pipeline": None
}

def capture_loop():
    """
    主捕捉與檢測循環，驅動 AgentPipeline。
    """
    logger.info("Starting Agent Pipeline capture loop")
    
    pipeline = AgentPipeline(state)
    service_context["pipeline"] = pipeline
    
    state.update_status(connected=True)
    
    last_fps_time = time.time()
    frame_count = 0
    
    try:
        while True:
            start_time = time.time()
            
            # 執行流水線循環 (AI 與 暫停邏輯已在 pipeline 內處理)
            processed_frame = pipeline.run_cycle()
            if processed_frame is not None:
                state.update_frame(processed_frame)

            # 計算並更新 FPS
            frame_count += 1
            now = time.time()
            if now - last_fps_time >= 1.0:
                state.update_status(fps=frame_count)
                frame_count = 0
                last_fps_time = now

            # FPS 鎖定 (30 FPS)
            elapsed = time.time() - start_time
            if elapsed < 1.0/30.0:
                time.sleep(1.0/30.0 - elapsed)
                
    except Exception as e:
        logger.exception(f"Unexpected error in capture loop: {e}")
    finally:
        logger.info("Stopping pipeline and releasing resources")
        pipeline.stop()
        state.update_status(connected=False)

def generate_mjpeg_stream():
    while True:
        frame = state.get_frame()
        if frame is None:
            # Generate a black placeholder image with text
            import numpy as np
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "CAMERA OFFLINE OR LOADING...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            time.sleep(1.0) # Slow down placeholder streaming
            
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        time.sleep(0.033)

# --- Routes ---

@app.route('/')
def index():
    return render_template('monitor.html', active_page='monitor')

@app.route('/camera')
def serve_camera():
    return render_template('camera.html', active_page='camera')

@app.route('/skills')
def serve_skills():
    return render_template('skills.html', active_page='skills')

@app.route('/events')
def serve_events():
    return render_template('events.html', active_page='events')

@app.route('/apps', strict_slashes=False)
def serve_apps_launcher():
    return render_template('apps_launcher.html', active_page='apps')

@app.route('/app/<filename>')
def serve_app(filename):
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-'))
    return render_template(f'apps/{safe_filename}.html', active_page='apps')

@app.route('/tailwind.js')
def serve_tailwind():
    return send_from_directory(WEB_DIR, 'tailwind.js')

@app.route('/live')
@app.route('/video_feed')
def video_feed():
    return Response(generate_mjpeg_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')




@app.route('/status')
def status():
    status_data = state.get_status().model_dump()
    status_data['local_ip'] = get_local_ip()
    status_data['prefs'] = state.prefs
    return jsonify(status_data)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        s = state.get_status()
        return jsonify({
            "threshold": s.threshold,
            "yaw_tolerance": s.yaw_tolerance,
            "sway_threshold": s.sway_threshold,
            "lean_threshold": s.lean_threshold,
            "camera_source": s.camera_source,
            "flip_enabled": s.flip_enabled
        })
    
    try:
        data = SettingsUpdate(**request.get_json())
        update_dict = {}
        if data.threshold is not None:
            update_dict["threshold"] = data.threshold
        if data.yaw_tolerance is not None:
            update_dict["yaw_tolerance"] = data.yaw_tolerance
        if data.sway_threshold is not None:
            update_dict["sway_threshold"] = data.sway_threshold
        if data.lean_threshold is not None:
            update_dict["lean_threshold"] = data.lean_threshold
        if data.camera_source is not None:
            update_dict["camera_source"] = data.camera_source
        if data.flip_enabled is not None:
            update_dict["flip_enabled"] = data.flip_enabled
            
        if update_dict:
            state.save_prefs(update_dict)
            
        return jsonify({"success": True})
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

@app.route('/mobile')
def serve_mobile():
    return send_from_directory(WEB_DIR, 'MobileCamera.html')

@app.route('/cameras')
def get_cameras():
    import subprocess
    import platform
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

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    try:
        data = request.data
        if not data:
            return jsonify({"error": "No image data"}), 400
        import numpy as np
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({"error": "Invalid image format"}), 400
        state.update_network_frame(frame)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error processing uploaded frame: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/recalibrate', methods=['POST'])
def recalibrate():
    pipeline = service_context.get("pipeline")
    if pipeline:
        pipeline.wizard.reset()
        pipeline.is_calibrated = False
        pipeline.baseline_eye_distance = 0.0
        pipeline.baseline_nose_chin_distance = 0.0
        pipeline.baseline_shoulder_width = 0.0
        pipeline.baseline_face_landmarks = None
        pipeline.baseline_pose_landmarks = None
        state.update_status(calibrating=True, calibration_progress=0)
        return jsonify({"success": True})
    return jsonify({"error": "Pipeline not initialized"}), 500

@app.route('/control', methods=['POST'])
def control():
    try:
        cmd = ControlCommand(**request.get_json())
        state.update_status(is_active=cmd.active)
        return jsonify({"success": True})
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

import shutil

@app.route('/api/skills', methods=['GET'])
def list_skills():
    try:
        skills_dir = os.path.join(PROJECT_ROOT, 'skills')
        if not os.path.exists(skills_dir):
            os.makedirs(skills_dir, exist_ok=True)
        results = []
        for d in os.listdir(skills_dir):
            cfg_path = os.path.join(skills_dir, d, 'config.json')
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                        results.append(cfg)
                except Exception as ex:
                    logger.error(f"Error reading skill {d} config: {ex}")
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/skills/create', methods=['POST'])
def create_skill():
    try:
        req_data = request.get_json()
        name = req_data.get("name")
        description = req_data.get("description", "")
        requirements = req_data.get("requirements", {"face_mesh": True, "pose": False})
        rules = req_data.get("rules", [])
        default_prefs = req_data.get("default_preferences", {"threshold": 0.10})
        is_update = req_data.get("is_update", False)
        
        rule_syntax = req_data.get("rule_syntax", "")
        
        if not name:
            return jsonify({"error": "Skill name is required"}), 400
            
        # Clean name to safe folder name
        safe_name = "".join([c for c in name if c.isalnum() or c in ('_', '-')]).lower()
        if not safe_name:
            return jsonify({"error": "Invalid skill name"}), 400
            
        skills_dir = os.path.join(PROJECT_ROOT, 'skills')
        target_dir = os.path.join(skills_dir, safe_name)
        if os.path.exists(target_dir) and not is_update:
            return jsonify({"error": f"Skill '{safe_name}' already exists"}), 400
            
        os.makedirs(target_dir, exist_ok=True)
        
        # Write config.json
        cfg = {
            "name": safe_name,
            "description": description,
            "enabled": True,
            "requirements": requirements,
            "default_preferences": default_prefs,
            "rule_syntax": rule_syntax,
            "rules": rules
        }
        with open(os.path.join(target_dir, 'config.json'), 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            
        # The action engine will use GenericActionDetector automatically if logic.py is missing.
        
        # Trigger reload in action engine
        pipeline = service_context.get("pipeline")
        if pipeline and hasattr(pipeline, 'action_engine'):
            pipeline.action_engine.load_action_skills()
            
        return jsonify({"success": True, "skill": cfg})
    except Exception as e:
        logger.error(f"Error creating skill: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/skills/toggle', methods=['POST'])
def toggle_skill():
    try:
        req_data = request.get_json()
        name = req_data.get("name")
        enabled = req_data.get("enabled", True)
        
        if not name:
            return jsonify({"error": "Skill name is required"}), 400
            
        skills_dir = os.path.join(PROJECT_ROOT, 'skills')
        cfg_path = os.path.join(skills_dir, name, 'config.json')
        if not os.path.exists(cfg_path):
            return jsonify({"error": f"Skill '{name}' not found"}), 404
            
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            
        cfg["enabled"] = enabled
        
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            
        # Trigger reload in action engine
        pipeline = service_context.get("pipeline")
        if pipeline and hasattr(pipeline, 'action_engine'):
            pipeline.action_engine.load_action_skills()
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/skills/delete', methods=['POST'])
def delete_skill():
    try:
        req_data = request.get_json()
        name = req_data.get("name")
        
        if not name:
            return jsonify({"error": "Skill name is required"}), 400
            
        # Removing built-in specific skill protection to support generic architecture
            
        skills_dir = os.path.join(PROJECT_ROOT, 'skills')
        target_dir = os.path.join(skills_dir, name)
        if not os.path.exists(target_dir):
            return jsonify({"error": f"Skill '{name}' not found"}), 404
            
        shutil.rmtree(target_dir)
        
        # Trigger reload in action engine
        pipeline = service_context.get("pipeline")
        if pipeline and hasattr(pipeline, 'action_engine'):
            pipeline.action_engine.load_action_skills()
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/events', methods=['GET'])
def list_events():
    try:
        events_dir = os.path.join(PROJECT_ROOT, 'events')
        if not os.path.exists(events_dir):
            os.makedirs(events_dir, exist_ok=True)
        results = []
        for d in os.listdir(events_dir):
            cfg_path = os.path.join(events_dir, d, 'config.json')
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                        results.append(cfg)
                except Exception as ex:
                    logger.error(f"Error reading event {d} config: {ex}")
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/create', methods=['POST'])
def create_event():
    try:
        req_data = request.get_json()
        name = req_data.get("name")
        description = req_data.get("description", "")
        rule_syntax = req_data.get("rule_syntax", "")
        rules = req_data.get("rules", [])
        is_update = req_data.get("is_update", False)
        
        # Backwards compatibility fallback: extract rule_syntax from rules list if empty
        if not rule_syntax:
            if isinstance(rules, list) and len(rules) > 0:
                rule_syntax = rules[0]
            elif isinstance(rules, str):
                rule_syntax = rules
                
        if not name:
            return jsonify({"error": "Event name is required"}), 400
        if not rule_syntax:
            return jsonify({"error": "Rule syntax is required"}), 400
            
        safe_name = "".join([c for c in name if c.isalnum() or c in ('_', '-')]).lower()
        if not safe_name:
            return jsonify({"error": "Invalid event name"}), 400
            
        events_dir = os.path.join(PROJECT_ROOT, 'events')
        target_dir = os.path.join(events_dir, safe_name)
        if os.path.exists(target_dir) and not is_update:
            return jsonify({"error": f"Event rule '{safe_name}' already exists"}), 400
            
        os.makedirs(target_dir, exist_ok=True)
        
        cfg = {
            "name": safe_name,
            "description": description,
            "enabled": True,
            "rule_syntax": rule_syntax,
            "rules": [rule_syntax]  # Keep rules list for frontend display
        }
        with open(os.path.join(target_dir, 'config.json'), 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            
        # Trigger reload in event engine
        pipeline = service_context.get("pipeline")
        if pipeline and hasattr(pipeline, 'event_engine'):
            pipeline.event_engine.reload()
            
        return jsonify({"success": True, "event": cfg})
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/toggle', methods=['POST'])
def toggle_event():
    try:
        req_data = request.get_json()
        name = req_data.get("name")
        enabled = req_data.get("enabled", True)
        
        if not name:
            return jsonify({"error": "Event name is required"}), 400
            
        events_dir = os.path.join(PROJECT_ROOT, 'events')
        cfg_path = os.path.join(events_dir, name, 'config.json')
        if not os.path.exists(cfg_path):
            return jsonify({"error": f"Event '{name}' not found"}), 404
            
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            
        cfg["enabled"] = enabled
        
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            
        pipeline = service_context.get("pipeline")
        if pipeline and hasattr(pipeline, 'event_engine'):
            pipeline.event_engine.reload()
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/delete', methods=['POST'])
def delete_event():
    try:
        req_data = request.get_json()
        name = req_data.get("name")
        
        if not name:
            return jsonify({"error": "Event name is required"}), 400
            
        events_dir = os.path.join(PROJECT_ROOT, 'events')
        target_dir = os.path.join(events_dir, name)
        if not os.path.exists(target_dir):
            return jsonify({"error": f"Event '{name}' not found"}), 404
            
        shutil.rmtree(target_dir)
        
        pipeline = service_context.get("pipeline")
        if pipeline and hasattr(pipeline, 'event_engine'):
            pipeline.event_engine.reload()
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/apps', methods=['GET'])
def list_apps():
    try:
        apps_dir = os.path.join(WEB_DIR, 'apps')
        if not os.path.exists(apps_dir):
            os.makedirs(apps_dir, exist_ok=True)
            
        results = []
        for file in os.listdir(apps_dir):
            if file.endswith('.html'):
                file_path = os.path.join(apps_dir, file)
                app_id = file[:-5]
                title = app_id
                description = "無說明 / No description"
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        t_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
                        if t_match:
                            title = t_match.group(1).strip()
                            
                        d_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', content, re.IGNORECASE)
                        if d_match:
                            description = d_match.group(1).strip()
                except Exception as ex:
                    logger.error(f"Error reading app {file}: {ex}")
                    
                results.append({
                    "id": app_id,
                    "title": title,
                    "description": description
                })
                
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings/update', methods=['POST'])
def api_update_settings():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No settings data provided"}), 400
            
        # Update state preferences directly
        state.save_prefs(data)
                
        return jsonify({"success": True, "prefs": state.prefs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def main():
    parser = argparse.ArgumentParser(description='RenUniversal Agent-Powered Server')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    
    # 啟動背景線程驅動流水線
    thread = threading.Thread(target=capture_loop, daemon=True)
    thread.start()
    
    local_ip = get_local_ip()
    
    # 啟動 HTTPS 背景伺服器 (以支援手機端瀏覽器的 Secure Context)
    def run_https():
        try:
            logger.info("Starting HTTPS Server on port 8443 for Secure Context (Local Wi-Fi)...")
            app.run(host='0.0.0.0', port=8443, ssl_context='adhoc', threaded=True)
        except Exception as e:
            logger.error(f"Failed to start HTTPS server: {e}")
            
    https_thread = threading.Thread(target=run_https, daemon=True)
    https_thread.start()
    
    logger.info(f"RenUniversal Agent Server starting on http://localhost:{args.port}")
    logger.info(f"Mobile Access URL (HTTP): http://{local_ip}:{args.port}/mobile")
    logger.info(f"Mobile Access URL (HTTPS Local): https://{local_ip}:8443/mobile")
    start_tunnel(args.port)
    app.run(host='0.0.0.0', port=args.port, threaded=True)


import signal
import sys

def graceful_shutdown(signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    if "pipeline" in service_context and service_context["pipeline"]:
        service_context["pipeline"].stop()
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

if __name__ == "__main__":
    main()
