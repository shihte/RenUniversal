import os
import time
import argparse
import threading
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
import cv2

# 導入重構後的核心模組
from core import SharedState, VideoStream, PostureDetector
import mediapipe.python.solutions.face_mesh as mp_face_mesh

app = Flask(__name__)
CORS(app)

# 初始化共享狀態與全域變數
state = SharedState()
detector_instance = None

# 路徑定義
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

def capture_loop(camera_id: int, threshold: float, yaw_tolerance: float):
    """主捕捉與檢測循環。"""
    global detector_instance
    
    cap = VideoStream(src=camera_id).start()
    time.sleep(1.0) # 預熱
    
    if not cap.is_opened():
        print(f"Error: Could not open webcam {camera_id}")
        state.update_status({"connected": False})
        return

    # 初始化偵測器
    detector = PostureDetector(state, threshold_ratio=threshold, yaw_tolerance=yaw_tolerance)
    detector_instance = detector
    
    state.update_status({"connected": True})
    
    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
        
        while not cap.stopped:
            start_time = time.time()
            frame = cap.read()
            if frame is None:
                continue

            # 如果偵測已啟動則進行處理
            if state.get_status().get("is_active", True):
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
                
    cap.stop()

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
    return jsonify(state.get_status())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        s = state.get_status()
        return jsonify({
            "threshold": s.get("threshold"),
            "yaw_tolerance": s.get("yaw_tolerance")
        })
    
    # POST 更新
    data = request.get_json()
    if detector_instance:
        if 'threshold' in data:
            detector_instance.threshold_ratio = float(data['threshold']) / 100.0
        if 'yaw_tolerance' in data:
            detector_instance.yaw_tolerance = float(data['yaw_tolerance']) / 100.0
        return jsonify({"success": True})
    return jsonify({"error": "Detector not initialized"}), 500

@app.route('/recalibrate', methods=['POST'])
def recalibrate():
    if detector_instance:
        detector_instance.recalibrate()
        return jsonify({"success": True})
    return jsonify({"error": "Detector not initialized"}), 500

@app.route('/control', methods=['POST'])
def control():
    data = request.get_json()
    if 'active' in data:
        state.update_status({"is_active": bool(data['active'])})
        return jsonify({"success": True})
    return jsonify({"error": "Invalid request"}), 400

def main():
    parser = argparse.ArgumentParser(description='CTAR Posture Monitor Modern Server')
    parser.add_argument('--threshold', type=float, default=0.20)
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--yaw-tolerance', type=float, default=0.10)
    args = parser.parse_args()
    
    # 啟動背景線程
    thread = threading.Thread(
        target=capture_loop, 
        args=(args.camera, args.threshold, args.yaw_tolerance), 
        daemon=True
    )
    thread.start()
    
    print(f"Server starting on http://localhost:{args.port}")
    app.run(host='0.0.0.0', port=args.port, threaded=True)

if __name__ == "__main__":
    main()
