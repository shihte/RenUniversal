import cv2
import mediapipe as mp
import numpy as np
import time
import math

class PostureMonitor:
    def __init__(self, threshold_ratio=2.0, camera_id=0):
        # Threshold: Ratio of (Chin-Nose Y) / (Nose-Eye Y) that indicates "looking down"
        self.threshold_ratio = threshold_ratio 
        self.camera_id = camera_id
        
        # MediaPipe Setup
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # Posture Counters
        self.down_count = 0
        
        # State Flags
        self.is_down = False
        
        # Timing
        self.prev_time = 0
        
        # Smoothing (Exponential Moving Average)
        self.smooth_ratio = 0
        self.alpha = 0.3  # Smoothing factor
        
        # Landmark indices for 2D ratio calculation
        self.NOSE = 1
        self.CHIN = 152
        self.LEFT_EYE = 33
        self.RIGHT_EYE = 263

    def calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def get_ratio(self, face_landmarks, w, h):
        """
        Calculate vertical ratio to detect looking down.
        Ratio = (Chin Y - Nose Y) / (Nose Y - Eye Y)
        
        When looking down:
        - Nose moves UP in frame (closer to eyes)
        - Chin moves DOWN in frame (further from nose)
        - So (Chin-Nose) increases and (Nose-Eye) decreases
        - Net result: Ratio INCREASES
        
        When turning head:
        - All Y coordinates shift similarly
        - Ratio stays relatively stable
        """
        # Get landmark positions
        nose = face_landmarks.landmark[self.NOSE]
        chin = face_landmarks.landmark[self.CHIN]
        left_eye = face_landmarks.landmark[self.LEFT_EYE]
        right_eye = face_landmarks.landmark[self.RIGHT_EYE]
        
        # Use Y coordinates (vertical position)
        # Note: In image coordinates, Y increases downward
        nose_y = nose.y * h
        chin_y = chin.y * h
        eye_y = (left_eye.y + right_eye.y) / 2 * h  # Average of both eyes
        
        # Get pixel positions for drawing
        nose_pt = (nose.x * w, nose.y * h)
        chin_pt = (chin.x * w, chin.y * h)
        left_eye_pt = (left_eye.x * w, left_eye.y * h)
        right_eye_pt = (right_eye.x * w, right_eye.y * h)
        
        # Calculate vertical distances
        chin_to_nose = chin_y - nose_y  # Distance from nose to chin
        nose_to_eye = nose_y - eye_y    # Distance from eye to nose
        
        # Avoid division by zero
        if nose_to_eye <= 0:
            return None
        
        ratio = chin_to_nose / nose_to_eye
        return ratio, (nose_pt, chin_pt, left_eye_pt, right_eye_pt)

    def process_frame(self, frame, face_mesh):
        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(img_rgb)
        
        current_ratio = None
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Get ratio
            result = self.get_ratio(face_landmarks, w, h)
            
            if result is not None:
                ratio, (nose_pt, chin_pt, left_eye_pt, right_eye_pt) = result
                
                # Smoothing
                if self.smooth_ratio == 0:
                    self.smooth_ratio = ratio
                else:
                    self.smooth_ratio = self.alpha * ratio + (1 - self.alpha) * self.smooth_ratio
                
                current_ratio = self.smooth_ratio
                
                # Draw landmarks for visualization
                cv2.circle(frame, (int(nose_pt[0]), int(nose_pt[1])), 5, (0, 255, 255), -1)  # Nose - Yellow
                cv2.circle(frame, (int(chin_pt[0]), int(chin_pt[1])), 5, (0, 255, 0), -1)    # Chin - Green
                cv2.circle(frame, (int(left_eye_pt[0]), int(left_eye_pt[1])), 5, (255, 0, 0), -1)  # Left Eye - Blue
                cv2.circle(frame, (int(right_eye_pt[0]), int(right_eye_pt[1])), 5, (255, 0, 0), -1)  # Right Eye - Blue
                
                # Draw lines
                cv2.line(frame, (int(nose_pt[0]), int(nose_pt[1])), (int(chin_pt[0]), int(chin_pt[1])), (0, 255, 0), 2)
                cv2.line(frame, (int(left_eye_pt[0]), int(left_eye_pt[1])), (int(right_eye_pt[0]), int(right_eye_pt[1])), (255, 0, 0), 2)
                
                # Logic: Check if ratio exceeds threshold (Looking Down)
                is_posture_bad = False
                
                if current_ratio > self.threshold_ratio:
                    is_posture_bad = True

                if is_posture_bad:
                    if not self.is_down:
                        self.down_count += 1
                        self.is_down = True
                    
                    cv2.putText(frame, "Bad Posture (Looking Down)", (50, 200),
                                cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                else:
                    self.is_down = False

                # Display Info
                color = (0, 0, 255) if is_posture_bad else (0, 255, 255)
                cv2.putText(frame, f"Ratio: {current_ratio:.2f}", (50, 150),
                            cv2.FONT_HERSHEY_PLAIN, 2, color, 2)
                cv2.putText(frame, f"Limit: > {self.threshold_ratio}", (w - 250, 80),
                            cv2.FONT_HERSHEY_PLAIN, 1.5, (200, 200, 200), 2)

        return frame

    def run(self):
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        print("Starting 2D Vertical Ratio Posture Monitor...")
        print(f"Ratio Threshold: > {self.threshold_ratio}")
        print("(Chin-Nose Y) / (Nose-Eye Y) ratio")
        
        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as face_mesh:
            
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    continue

                frame = self.process_frame(frame, face_mesh)
                
                # Mirror
                frame = cv2.flip(frame, 1)
                
                # FPS
                curr_time = time.time()
                fps = 1 / (curr_time - self.prev_time) if self.prev_time else 0
                self.prev_time = curr_time
                
                h, w, _ = frame.shape
                cv2.putText(frame, f"FPS: {int(fps)}", (w - 150, 50), 
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                cv2.putText(frame, f"Count: {self.down_count}", (50, 100),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

                cv2.imshow('Posture Monitor (2D Ratio)', frame)
                
                if cv2.waitKey(5) & 0xFF == 27:
                    break
        
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='2D Ratio-Based Posture Monitor')
    parser.add_argument('--threshold', type=float, default=2.0, help='Ratio threshold (Default 2.0).')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID (default 0).')
    
    args = parser.parse_args()
    
    monitor = PostureMonitor(threshold_ratio=args.threshold, camera_id=args.camera)
    monitor.run()