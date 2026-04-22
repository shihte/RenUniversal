import os
import time
import argparse
import threading
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
import cv2
from loguru import logger
from pydantic import ValidationError

# 導入重構後的核心模組與 Schema
from core import SharedState, VideoStream, PostureDetector
from core.schema import SettingsUpdate, ControlCommand
import mediapipe.python.solutions.face_mesh as mp_face_mesh

app = Flask(__name__)
CORS(app)

# 初始化共享狀態
state = SharedState()

# 路徑定義
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# 全局偵測組件容器 (代替 global 變數)
service_context = {
    "detector": None
}

def capture_loop(camera_id: int, threshold: float, yaw_tolerance: float):
    """
    主捕捉與檢測循環。
    遵循 Pattern: Defensive Error Handling 與 Observability。
    """
    logger.info(f"Starting capture loop on camera {camera_id}")
    
    cap = VideoStream(src=camera_id).start()
    time.sleep(1.0) # 預熱
    
    if not cap.is_opened():
        logger.error(f"Could not open webcam {camera_id}")
        state.update_status(connected=False)
        return

    # 初始化偵測器並存入 context
    detector = PostureDetector(state, threshold_ratio=threshold, yaw_tolerance=yaw_tolerance)
    service_context["detector"] = detector
    
    state.update_status(connected=True)
    
    try:
        with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as face_mesh:
            
            while not cap.stopped:
                start_time = time.time()
                frame = cap.read()
                
                if frame is None:
                    # VideoStream 內部具備自動重連，此處僅需等待
                    time.sleep(0.01)
                    continue

                # 如果偵測已啟動則進行處理
                if state.get_status().is_active:
                    processed_frame = detector.process_frame(frame, face_mesh)
                    state.update_frame(processed_frame)
                else:
                    # 暫停模式：顯示變暗的影像
                    dimmed = cv2.addWeighted(frame, 0.5, frame, 0, 0)
                    state.update_frame(dimmed)

                # FPS 鎖定 (30 FPS)
                elapsed = time.time() - start_time
                if elapsed < 1.0/30.0:
                    time.sleep(1.0/30.0 - elapsed)
    except Exception as e:
        logger.exception(f"Unexpected error in capture loop: {e}")
    finally:
        logger.info("Stopping capture loop and releasing resources")
        cap.stop()
        state.update_status(connected=False)

def generate_mjpeg_stream():
    """MJPEG 串流生成器。"""
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
    # 透過 Pydantic model_dump 轉為字典
    return jsonify(state.get_status().model_dump())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    detector = service_context.get("detector")
    if not detector:
        return jsonify({"error": "Detector not initialized"}), 500

    if request.method == 'GET':
        s = state.get_status()
        return jsonify({
            "threshold": s.threshold,
            "yaw_tolerance": s.yaw_tolerance
        })
    
    # POST 更新：強型別驗證 (Pattern: Strongly Typed I/O)
    try:
        data = SettingsUpdate(**request.get_json())
        if data.threshold is not None:
            detector.threshold_ratio = data.threshold / 100.0
            state.update_status(threshold=data.threshold)
        if data.yaw_tolerance is not None:
            detector.yaw_tolerance = data.yaw_tolerance / 100.0
            state.update_status(yaw_tolerance=data.yaw_tolerance)
            
        logger.info(f"Settings updated: {data}")
        return jsonify({"success": True})
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

@app.route('/recalibrate', methods=['POST'])
def recalibrate():
    detector = service_context.get("detector")
    if detector:
        detector.recalibrate()
        return jsonify({"success": True})
    return jsonify({"error": "Detector not initialized"}), 500

@app.route('/control', methods=['POST'])
def control():
    try:
        cmd = ControlCommand(**request.get_json())
        state.update_status(is_active=cmd.active)
        logger.info(f"Control command received: active={cmd.active}")
        return jsonify({"success": True})
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

def main():
    parser = argparse.ArgumentParser(description='CTAR Posture Monitor Refactored Server')
    parser.add_argument('--threshold', type=float, default=20.0) # 改為百分比預設
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--yaw-tolerance', type=float, default=10.0)
    args = parser.parse_args()
    
    # 初始化配置
    state.update_status(
        threshold=args.threshold,
        yaw_tolerance=args.yaw_tolerance
    )
    
    # 啟動背景線程
    thread = threading.Thread(
        target=capture_loop, 
        # 將百分比轉回小數傳給 detector
        args=(args.camera, args.threshold / 100.0, args.yaw_tolerance / 100.0), 
        daemon=True
    )
    thread.start()
    
    logger.info(f"Server starting on http://localhost:{args.port}")
    app.run(host='0.0.0.0', port=args.port, threaded=True)

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
