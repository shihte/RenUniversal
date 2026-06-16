"""
CTAR Posture Monitor - Flask MJPEG Streaming Server

This server captures webcam video, processes it with MediaPipe for posture detection,
and streams the annotated video as MJPEG to the frontend.

Features:
- 3-second calibration phase to establish baseline eye distance
- Yaw filtering to ignore head turns
- Nose-chin distance based head-down detection

Optimizations:
- Threaded webcam capture
- Resized inference (640x360) for speed
- Disabled iris tracking (refine_landmarks=False)

Architecture:
- Single Server on Port 8080
- /game: Serves the Game.html
- /live: Serves the video stream
- /status: Serves the posture status JSON

Usage:
    python stream_server.py [--threshold 0.15] [--camera 0] [--port 8080]

Endpoints:
    /           - Health check
    /video_feed - MJPEG video stream
    /status     - Current posture status as JSON
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import math
import argparse
import threading
import os
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend

# Global variables for sharing data between threads
current_frame = None
current_status = {
    "ratio": 0,
    "nose_chin_ratio": 0,
    "is_bad_posture": False,
    "down_count": 0,
    "fps": 0,
    "connected": False,
    "calibrating": True,
    "calibration_progress": 0,
    "is_turning": False,
    "baseline_eye_dist": 0,
    "threshold": 0.30,
    "yaw_tolerance": 0.20
}
frame_lock = threading.Lock()
status_lock = threading.Lock()

# Global monitor instance for runtime settings changes
monitor_instance = None

# Helper to locate resources relative to this script
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# ==================== Helper Class ====================
class WebcamStream:
    """Threaded webcam capture to improve FPS."""
    def __init__(self, src=0, width=1280, height=720):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduce latency
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

class PostureMonitor:
    """Posture Monitor with calibration and yaw filtering."""
    
    def __init__(self, threshold_ratio=0.15, camera_id=0, yaw_tolerance=0.25):
        """
        Args:
            threshold_ratio: How much nose-chin distance needs to DECREASE to detect head-down
                            (as a fraction of baseline, e.g., 0.15 = 15% decrease)
            camera_id: Camera device ID
            yaw_tolerance: How much eye distance can deviate from baseline before ignoring
                          (as a fraction, e.g., 0.25 = 25% deviation allowed)
        """
        self.threshold_ratio = threshold_ratio
        self.camera_id = camera_id
        self.yaw_tolerance = yaw_tolerance
        
        # MediaPipe Setup
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # Calibration
        self.calibration_duration = 3.0  # seconds
        self.calibration_start_time = None
        self.is_calibrated = False
        self.baseline_eye_distance = 0
        self.baseline_nose_chin_distance = 0
        self.calibration_samples_eye = []
        self.calibration_samples_nose_chin = []
        
        # Posture Counters
        self.down_count = 0
        
        # State Flags
        self.is_down = False
        self.is_turning = False
        
        # Timing
        self.prev_time = 0
        
        # Smoothing (Exponential Moving Average)
        self.smooth_nose_chin = 0
        self.alpha = 0.3
        
        # Landmark indices
        self.NOSE = 1
        self.CHIN = 152
        self.LEFT_EYE = 33
        self.RIGHT_EYE = 263
        
        # Running flag
        self.running = False
        self.active = True  # Controls detection ON/OFF while keeping stream alive

    def calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def get_metrics(self, face_landmarks, w, h):
        """Get eye distance and nose-chin distance for detection."""
        nose = face_landmarks.landmark[self.NOSE]
        chin = face_landmarks.landmark[self.CHIN]
        left_eye = face_landmarks.landmark[self.LEFT_EYE]
        right_eye = face_landmarks.landmark[self.RIGHT_EYE]
        
        # Pixel positions
        nose_pt = (nose.x * w, nose.y * h)
        chin_pt = (chin.x * w, chin.y * h)
        left_eye_pt = (left_eye.x * w, left_eye.y * h)
        right_eye_pt = (right_eye.x * w, right_eye.y * h)
        
        # Use HORIZONTAL eye distance for yaw detection
        # This won't change when looking up/down, only when turning left/right
        eye_horizontal_distance = abs(right_eye_pt[0] - left_eye_pt[0])
        
        # Use full distance for nose-chin (affected by head tilt)
        nose_chin_distance = self.calculate_distance(nose_pt, chin_pt)
        
        return {
            "eye_distance": eye_horizontal_distance,
            "nose_chin_distance": nose_chin_distance,
            "points": (nose_pt, chin_pt, left_eye_pt, right_eye_pt)
        }

    def process_frame(self, frame, face_mesh):
        """Process a single frame and return annotated frame.
           OPTIMIZATION: Resizes frame for inference but draws on original.
        """
        global current_status
        
        # If detection is paused, just return the frame (dimmed) and update basic status
        if not self.active:
            # Dim the frame to indicate inactivity
            dimmed = cv2.addWeighted(frame, 0.5, np.zeros(frame.shape, frame.dtype), 0, 0)
            cv2.putText(dimmed, "DETECTION PAUSED", (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (100, 100, 100), 2)
            
            with status_lock:
                current_status.update({
                    "is_active": False,
                    "fps": 30, # Fake FPS
                    "connected": True
                })
            return dimmed

        h, w, _ = frame.shape
        
        # Optimization: Resize for inference
        inference_w, inference_h = 640, 360
        frame_small = cv2.resize(frame, (inference_w, inference_h))
        img_rgb_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        
        results = face_mesh.process(img_rgb_small)
        
        is_posture_bad = False
        nose_chin_ratio = 0
        calibration_progress = 0
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            # Pass original w, h so points map back to the high-res frame
            metrics = self.get_metrics(face_landmarks, w, h)
            
            eye_dist = metrics["eye_distance"]
            nose_chin_dist = metrics["nose_chin_distance"]
            nose_pt, chin_pt, left_eye_pt, right_eye_pt = metrics["points"]
            
            # === CALIBRATION PHASE ===
            if not self.is_calibrated:
                if self.calibration_start_time is None:
                    self.calibration_start_time = time.time()
                
                elapsed = time.time() - self.calibration_start_time
                calibration_progress = min(elapsed / self.calibration_duration, 1.0)
                
                # Collect samples
                self.calibration_samples_eye.append(eye_dist)
                self.calibration_samples_nose_chin.append(nose_chin_dist)
                
                # Draw calibration indicator
                cv2.putText(frame, f"Calibrating... {int(calibration_progress * 100)}%", 
                           (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
                cv2.putText(frame, "Please look straight ahead", 
                           (50, 90), cv2.FONT_HERSHEY_PLAIN, 1.5, (200, 200, 200), 2)
                
                # Progress bar
                bar_width = int(w * 0.6)
                bar_x = int((w - bar_width) / 2)
                bar_y = h - 50
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + 20), (100, 100, 100), -1)
                cv2.rectangle(frame, (bar_x, bar_y), 
                            (bar_x + int(bar_width * calibration_progress), bar_y + 20), (0, 255, 0), -1)
                
                if elapsed >= self.calibration_duration:
                    # Calculate baselines
                    self.baseline_eye_distance = np.mean(self.calibration_samples_eye)
                    self.baseline_nose_chin_distance = np.mean(self.calibration_samples_nose_chin)
                    
                    # Prevent division by zero
                    if self.baseline_eye_distance == 0: self.baseline_eye_distance = 1
                    if self.baseline_nose_chin_distance == 0: self.baseline_nose_chin_distance = 1
                    
                    self.is_calibrated = True
                    print(f"Calibration complete!")
                    print(f"  Baseline eye distance: {self.baseline_eye_distance:.2f}")
                    print(f"  Baseline nose-chin distance: {self.baseline_nose_chin_distance:.2f}")
            
            # === DETECTION PHASE ===
            else:
                # Check for head turning (yaw filtering)
                eye_deviation = abs(eye_dist - self.baseline_eye_distance) / self.baseline_eye_distance
                self.is_turning = eye_deviation > self.yaw_tolerance
                
                # Smoothing nose-chin distance
                if self.smooth_nose_chin == 0:
                    self.smooth_nose_chin = nose_chin_dist
                else:
                    self.smooth_nose_chin = self.alpha * nose_chin_dist + (1 - self.alpha) * self.smooth_nose_chin
                
                # Calculate ratio: how much nose-chin has changed from baseline
                # Negative = head down (nose-chin gets shorter due to perspective)
                nose_chin_ratio = (self.smooth_nose_chin - self.baseline_nose_chin_distance) / self.baseline_nose_chin_distance
                
                # Draw landmarks
                if self.is_turning:
                    # Yellow when turning (ignored)
                    color = (0, 255, 255)
                else:
                    color = (0, 255, 0)
                
                cv2.circle(frame, (int(nose_pt[0]), int(nose_pt[1])), 5, (0, 255, 255), -1)
                cv2.circle(frame, (int(chin_pt[0]), int(chin_pt[1])), 5, color, -1)
                cv2.circle(frame, (int(left_eye_pt[0]), int(left_eye_pt[1])), 5, (255, 0, 0), -1)
                cv2.circle(frame, (int(right_eye_pt[0]), int(right_eye_pt[1])), 5, (255, 0, 0), -1)
                
                # Draw lines
                cv2.line(frame, (int(nose_pt[0]), int(nose_pt[1])), 
                        (int(chin_pt[0]), int(chin_pt[1])), color, 2)
                cv2.line(frame, (int(left_eye_pt[0]), int(left_eye_pt[1])), 
                        (int(right_eye_pt[0]), int(right_eye_pt[1])), (255, 0, 0), 2)
                
                # Only detect posture if not turning
                if not self.is_turning:
                    # Head down: nose-chin distance DECREASES (ratio becomes negative)
                    # We trigger when ratio < -threshold (e.g., -0.15 = 15% decrease)
                    if self.is_down:
                        if nose_chin_ratio > -self.threshold_ratio + 0.05:  # Hysteresis
                            self.is_down = False
                        else:
                            is_posture_bad = True
                    else:
                        if nose_chin_ratio < -self.threshold_ratio:
                            is_posture_bad = True
                            self.down_count += 1
                            self.is_down = True

        # Calculate FPS
        curr_time = time.time()
        fps = 1 / (curr_time - self.prev_time) if self.prev_time else 0
        self.prev_time = curr_time
        
        # Update global status
        with status_lock:
            current_status = {
                "ratio": float(round(nose_chin_ratio * 100, 1)),  # As percentage
                "nose_chin_ratio": float(round(nose_chin_ratio, 3)),
                "is_bad_posture": bool(is_posture_bad),
                "down_count": int(self.down_count),
                "fps": int(fps),
                "connected": True,
                "calibrating": bool(not self.is_calibrated),
                "calibration_progress": int(round(calibration_progress * 100)),
                "is_turning": bool(self.is_turning),
                "baseline_eye_dist": float(round(self.baseline_eye_distance, 1)),
                "threshold": float(round(self.threshold_ratio * 100)),
                "yaw_tolerance": float(round(self.yaw_tolerance * 100)),
                "is_active": bool(self.active)
            }
        
        # Mirror the frame
        return cv2.flip(frame, 1)

    def capture_loop(self):
        """Main capture loop running in separate thread."""
        global current_frame
        
        # Optimization: Use threaded WebcamStream
        cap = WebcamStream(src=self.camera_id).start()
        time.sleep(1.0) # Warmup
        
        if cap.stream.isOpened():
             pass # Stream started
        else:
            print("Error: Could not open webcam.")
            with status_lock:
                current_status["connected"] = False
            return

        print(f"Camera opened: ID {self.camera_id}")
        print(f"Threshold: {self.threshold_ratio * 100:.0f}% decrease in nose-chin distance")
        print(f"Yaw tolerance: {self.yaw_tolerance * 100:.0f}% deviation allowed")
        print("Starting 3-second calibration...")
        
        self.running = True
        
        # Optimization: refine_landmarks=False for speed
        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as face_mesh:
            
            while self.running:
                start_time = time.time()
                
                # Capture frame
                frame = cap.read()
                if frame is None:
                    continue

                processed_frame = self.process_frame(frame, face_mesh)
                
                with frame_lock:
                    current_frame = processed_frame.copy()

                # FPS Lock: Ensure we don't exceed 30 FPS (approx 33ms per frame)
                processing_time = time.time() - start_time
                target_frame_time = 1.0 / 30.0
                if processing_time < target_frame_time:
                    time.sleep(target_frame_time - processing_time)
        
        cap.stop()
        print("Camera released.")

    def stop(self):
        """Stop the capture loop."""
        self.running = False


def generate_frames():
    """Generator function for MJPEG streaming."""
    global current_frame
    
    while True:
        with frame_lock:
            if current_frame is None:
                # Generate placeholder frame
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Waiting for camera...", (150, 240),
                           cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
                frame = placeholder
            else:
                frame = current_frame.copy()
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS


@app.route('/')
def index():
    """Serve the Monitor Dashboard (Monitor.html)."""
    return send_from_directory(PROJECT_ROOT, 'Monitor.html')

@app.route('/game')
def serve_game():
    """Serve the Game.html file from the project root."""
    return send_from_directory(PROJECT_ROOT, 'Game.html')

@app.route('/live')
@app.route('/video_feed')
def video_feed():
    """MJPEG video stream endpoint."""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/status')
def status():
    """Return current posture status as JSON."""
    with status_lock:
        return jsonify(current_status)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Get or update detection settings."""
    global monitor_instance
    
    if request.method == 'GET':
        if monitor_instance:
            return jsonify({
                "threshold": float(round(monitor_instance.threshold_ratio * 100)),
                "yaw_tolerance": float(round(monitor_instance.yaw_tolerance * 100))
            })
        return jsonify({"error": "Monitor not initialized"}), 500
    
    # POST - update settings
    data = request.get_json()
    
    if monitor_instance:
        if 'threshold' in data:
            # Convert from percentage to fraction
            monitor_instance.threshold_ratio = float(data['threshold']) / 100.0
            print(f"Threshold updated to: {monitor_instance.threshold_ratio * 100}%")
        
        if 'yaw_tolerance' in data:
            monitor_instance.yaw_tolerance = float(data['yaw_tolerance']) / 100.0
            print(f"Yaw tolerance updated to: {monitor_instance.yaw_tolerance * 100}%")
        
        return jsonify({
            "success": True,
            "threshold": float(round(monitor_instance.threshold_ratio * 100)),
            "yaw_tolerance": float(round(monitor_instance.yaw_tolerance * 100))
        })
    
    return jsonify({"error": "Monitor not initialized"}), 500


@app.route('/recalibrate', methods=['POST'])
def recalibrate():
    """Trigger recalibration."""
    global monitor_instance
    
    if monitor_instance:
        monitor_instance.is_calibrated = False
        monitor_instance.calibration_start_time = None
        monitor_instance.calibration_samples_eye = []
        monitor_instance.calibration_samples_nose_chin = []
        print("Recalibration triggered")
        return jsonify({"success": True, "message": "Recalibration started"})
    
    return jsonify({"error": "Monitor not initialized"}), 500


@app.route('/control', methods=['POST'])
def control():
    """Control the detection loop (Pause/Resume)."""
    global monitor_instance
    data = request.get_json()
    
    if monitor_instance:
        if 'active' in data:
            monitor_instance.active = bool(data['active'])
            state = "Active" if monitor_instance.active else "Paused"
            print(f"Detection state changed to: {state}")
            return jsonify({"success": True, "active": monitor_instance.active})
    
    return jsonify({"error": "Monitor not initialized"}), 500


def main():
    parser = argparse.ArgumentParser(description='CTAR Posture Monitor Stream Server')
    parser.add_argument('--threshold', type=float, default=0.20, 
                        help='Head-down threshold as fraction (default 0.20 = 20%% decrease)')
    parser.add_argument('--camera', type=int, default=0, 
                        help='Camera ID (default 0)')
    parser.add_argument('--port', type=int, default=8080, 
                        help='Server port (default 8080)')
    parser.add_argument('--yaw-tolerance', type=float, default=0.10,
                        help='Yaw tolerance as fraction (default 0.10 = 10%% deviation)')
    
    args = parser.parse_args()
    
    # Create and start posture monitor in separate thread
    global monitor_instance
    monitor = PostureMonitor(
        threshold_ratio=args.threshold, 
        camera_id=args.camera,
        yaw_tolerance=args.yaw_tolerance
    )
    monitor_instance = monitor  # Set global reference for runtime settings
    capture_thread = threading.Thread(target=monitor.capture_loop, daemon=True)
    capture_thread.start()
    
    print(f"\n{'='*50}")
    print("CTAR Posture Monitor & Game Server")
    print(f"{'='*50}")
    print(f"Game URL:     http://localhost:{args.port}/game")
    print(f"Live Stream:  http://localhost:{args.port}/live")
    print(f"Status API:   http://localhost:{args.port}/status")
    print(f"{'='*50}\n")
    
    try:
        app.run(host='0.0.0.0', port=args.port, threaded=True)
    except KeyboardInterrupt:
        monitor.stop()
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
