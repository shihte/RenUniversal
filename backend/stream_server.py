"""
CTAR Posture Monitor - Flask MJPEG Streaming Server

This server captures webcam video, processes it with MediaPipe for posture detection,
and streams the annotated video as MJPEG to the frontend.

Features:
- 3-second calibration phase to establish baseline eye distance
- Yaw filtering to ignore head turns
- Nose-chin distance based head-down detection

Usage:
    python stream_server.py [--threshold 0.15] [--camera 0] [--port 5000]

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
from flask import Flask, Response, jsonify
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
    "baseline_eye_dist": 0
}
frame_lock = threading.Lock()
status_lock = threading.Lock()


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
        
        # Calculate distances
        eye_distance = self.calculate_distance(left_eye_pt, right_eye_pt)
        nose_chin_distance = self.calculate_distance(nose_pt, chin_pt)
        
        return {
            "eye_distance": eye_distance,
            "nose_chin_distance": nose_chin_distance,
            "points": (nose_pt, chin_pt, left_eye_pt, right_eye_pt)
        }

    def process_frame(self, frame, face_mesh):
        """Process a single frame and return annotated frame."""
        global current_status
        
        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(img_rgb)
        
        is_posture_bad = False
        nose_chin_ratio = 0
        calibration_progress = 0
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
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
                "baseline_eye_dist": float(round(self.baseline_eye_distance, 1))
            }
        
        # Mirror the frame
        return cv2.flip(frame, 1)

    def capture_loop(self):
        """Main capture loop running in separate thread."""
        global current_frame
        
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            with status_lock:
                current_status["connected"] = False
            return

        print(f"Camera opened: ID {self.camera_id}")
        print(f"Threshold: {self.threshold_ratio * 100:.0f}% decrease in nose-chin distance")
        print(f"Yaw tolerance: {self.yaw_tolerance * 100:.0f}% deviation allowed")
        print("Starting 3-second calibration...")
        
        self.running = True
        
        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as face_mesh:
            
            while self.running:
                success, frame = cap.read()
                if not success:
                    continue

                processed_frame = self.process_frame(frame, face_mesh)
                
                with frame_lock:
                    current_frame = processed_frame.copy()
        
        cap.release()
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
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "CTAR Posture Monitor Stream Server",
        "endpoints": {
            "/video_feed": "MJPEG video stream",
            "/status": "Current posture status"
        }
    })


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


def main():
    parser = argparse.ArgumentParser(description='CTAR Posture Monitor Stream Server')
    parser.add_argument('--threshold', type=float, default=0.12, 
                        help='Head-down threshold as fraction (default 0.12 = 12%% decrease)')
    parser.add_argument('--camera', type=int, default=0, 
                        help='Camera ID (default 0)')
    parser.add_argument('--port', type=int, default=5000, 
                        help='Server port (default 5000)')
    parser.add_argument('--yaw-tolerance', type=float, default=0.20,
                        help='Yaw tolerance as fraction (default 0.20 = 20%% deviation)')
    
    args = parser.parse_args()
    
    # Create and start posture monitor in separate thread
    monitor = PostureMonitor(
        threshold_ratio=args.threshold, 
        camera_id=args.camera,
        yaw_tolerance=args.yaw_tolerance
    )
    capture_thread = threading.Thread(target=monitor.capture_loop, daemon=True)
    capture_thread.start()
    
    print(f"\n{'='*50}")
    print("CTAR Posture Monitor Stream Server")
    print(f"{'='*50}")
    print(f"Video stream: http://localhost:{args.port}/video_feed")
    print(f"Status API:   http://localhost:{args.port}/status")
    print(f"{'='*50}\n")
    
    try:
        app.run(host='0.0.0.0', port=args.port, threaded=True)
    except KeyboardInterrupt:
        monitor.stop()
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
