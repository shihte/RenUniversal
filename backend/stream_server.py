import os
import time
import argparse
import threading
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
import cv2
from loguru import logger
from pydantic import ValidationError

from core import SharedState
from core.pipeline import AgentPipeline
from core.schema import SettingsUpdate, ControlCommand

app = Flask(__name__)
CORS(app)

# 初始化共享狀態 (具備 Memory 功能)
state = SharedState()

# 路徑定義
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

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
            
            # 如果偵測已啟動則執行流水線循環
            if state.get_status().is_active:
                processed_frame = pipeline.run_cycle()
                if processed_frame is not None:
                    state.update_frame(processed_frame)
            else:
                # 暫停模式：僅讀取影格但不處理分析
                frame_data = pipeline.capture.read()
                if frame_data.frame is not None:
                    dimmed = cv2.addWeighted(frame_data.frame, 0.5, frame_data.frame, 0, 0)
                    state.update_frame(dimmed)

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
            time.sleep(0.1)
            continue
            
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        time.sleep(0.033)

# --- Routes ---

@app.route('/')
def index():
    return send_from_directory(PROJECT_ROOT, 'Monitor.html')

@app.route('/game')
def serve_game():
    return send_from_directory(PROJECT_ROOT, 'Game.html')

@app.route('/live')
@app.route('/video_feed')
def video_feed():
    return Response(generate_mjpeg_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify(state.get_status().model_dump())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    pipeline = service_context.get("pipeline")
    if not pipeline:
        return jsonify({"error": "Pipeline not initialized"}), 500

    if request.method == 'GET':
        s = state.get_status()
        return jsonify({
            "threshold": s.threshold,
            "yaw_tolerance": s.yaw_tolerance
        })
    
    try:
        data = SettingsUpdate(**request.get_json())
        if data.threshold is not None:
            pipeline.reviewer.threshold_ratio = data.threshold / 100.0
            state.update_status(threshold=data.threshold)
            state.save_prefs({"threshold_ratio": data.threshold / 100.0})
            
        if data.yaw_tolerance is not None:
            pipeline.reviewer.yaw_tolerance = data.yaw_tolerance / 100.0
            state.update_status(yaw_tolerance=data.yaw_tolerance)
            state.save_prefs({"yaw_tolerance": data.yaw_tolerance / 100.0})
            
        return jsonify({"success": True})
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

@app.route('/recalibrate', methods=['POST'])
def recalibrate():
    pipeline = service_context.get("pipeline")
    if pipeline:
        pipeline.wizard.reset()
        pipeline.is_calibrated = False
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

def main():
    parser = argparse.ArgumentParser(description='CTAR Agent-Powered Server')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    
    # 啟動背景線程驅動流水線
    thread = threading.Thread(target=capture_loop, daemon=True)
    thread.start()
    
    logger.info(f"CTAR Agent Server starting on http://localhost:{args.port}")
    app.run(host='0.0.0.0', port=args.port, threaded=True)

if __name__ == "__main__":
    main()
