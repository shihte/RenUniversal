import cv2
import mediapipe as mp
import math
import time
import sys

class PostureMonitor:
    def __init__(self, threshold_angle=3.0, camera_id=0):
        self.threshold_angle = abs(threshold_angle) # Use absolute value
        self.camera_id = camera_id
        
        # We will now use absolute deviation Logic
        # logic: if abs(current_angle) > self.threshold_angle -> Bad Posture
        
        # MediaPipe Setup
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # State
        self.down_count = 0
        self.is_down = False
        self.prev_time = 0
        
        # Smoothing
        self.smooth_angle = None
        self.alpha = args.alpha if 'args' in globals() else 0.1  # Smoothing factor
        
        # Auto-Reset (Dynamic Stability)
        self.stable_ref_angle = 0.0 # The angle we are currently holding stable at
        self.stable_start_time = time.time()
        self.reset_duration = 3.0 # seconds
        self.zero_offset = 0.0 # Calibration offset

    def calculate_angle(self, p1, p2):
        """Calculates the angle of the vector p1->p2 relative to vertical (0, -1)."""
        x1, y1 = p1
        x2, y2 = p2
        vx = x2 - x1
        vy = y2 - y1
        return math.degrees(math.atan2(vx, -vy))

    def process_frame(self, frame, face_mesh):
        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(img_rgb)
        
        current_angle = None
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            pt_chin = face_landmarks.landmark[152]
            pt_fore = face_landmarks.landmark[10]
            
            x_chin, y_chin = int(pt_chin.x * w), int(pt_chin.y * h)
            x_fore, y_fore = int(pt_fore.x * w), int(pt_fore.y * h)

            # Calculate Angle (Raw)
            raw_angle = self.calculate_angle((x_chin, y_chin), (x_fore, y_fore))
            
            # Smoothing
            if self.smooth_angle is None:
                self.smooth_angle = raw_angle
                self.stable_ref_angle = raw_angle
            else:
                self.smooth_angle = self.alpha * raw_angle + (1 - self.alpha) * self.smooth_angle
            
            # Apply offset (Tare)
            current_angle = round(self.smooth_angle - self.zero_offset, 1)

            # Draw Visuals
            cv2.circle(frame, (x_chin, y_chin), 5, (0, 0, 255), -1)
            cv2.circle(frame, (x_fore, y_fore), 5, (0, 255, 0), -1)
            cv2.line(frame, (x_chin, y_chin), (x_fore, y_fore), (255, 0, 0), 2)
            
            self.mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
            )

            # Logic: Check Down
            # Absolute Deviation Logic
            # Assuming 0 is neutral. Any deviation > threshold is "Bad" (or at least "Down" if we ignore Looking Up)
            is_posture_bad = False
            if abs(current_angle) > self.threshold_angle:
                is_posture_bad = True

            if is_posture_bad:
                if not self.is_down:
                    self.down_count += 1
                    self.is_down = True
                
                cv2.putText(frame, "Bad Posture (Look Up)", (50, 200),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
            else:
                self.is_down = False

            # Dynamic Stability Reset Logic
            # Check if *actual smoothed angle* (not the offsetted one) is stable
            # This allows us to track stability of head movement regardless of current zero
            if abs(self.smooth_angle - self.stable_ref_angle) <= 1.0:
                elapsed = time.time() - self.stable_start_time
                if elapsed >= self.reset_duration:
                    # self.down_count = 0  <-- REMOVED: Count should persist
                    self.zero_offset = self.smooth_angle # Recalibrate/Tare!
                    
                    # Visual feedback
                    cv2.putText(frame, "RECALIBRATED!", (50, 300),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
                else:
                    # Show progress
                     if elapsed > 0.5:
                        cv2.putText(frame, f"Calibrating... {max(0, self.reset_duration - elapsed):.1f}s", (50, 300),
                                cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 0), 2)
            else:
                # Movement detected, reset stability reference
                self.stable_ref_angle = self.smooth_angle
                self.stable_start_time = time.time()

            # Display Angle
            # Determine color based on bad/good status
            color = (0, 0, 255) if is_posture_bad else (0, 255, 255)
            cv2.putText(frame, f"Angle: {current_angle} deg", (50, 150),
                        cv2.FONT_HERSHEY_PLAIN, 2, color, 2)
            
            # Display Threshold
            cv2.putText(frame, f"Limit: {self.threshold_angle}", (w - 200, 80),
                        cv2.FONT_HERSHEY_PLAIN, 1.5, (200, 200, 200), 2)

        return frame

    def run(self):
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        print("Starting Posture Monitor... Press 'ESC' to exit.")
        print(f"Threshold: {self.threshold_angle} (Absolute Deviation)")
        
        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        ) as face_mesh:
            
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    continue

                frame = cv2.flip(frame, 1) # Mirror view
                frame = self.process_frame(frame, face_mesh)

                curr_time = time.time()
                fps = 1 / (curr_time - self.prev_time) if (curr_time - self.prev_time) > 0 else 0
                self.prev_time = curr_time
                
                # Display FPS and Count
                if 'w' not in locals(): # Get width safely if not defined
                    h, w, _ = frame.shape
                
                cv2.putText(frame, f"FPS: {int(fps)}", (w - 150, 50), 
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                cv2.putText(frame, f"Count: {self.down_count}", (50, 100),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

                cv2.imshow('Posture Monitor (FaceMesh)', frame)

                if cv2.waitKey(5) & 0xFF == 27:
                    break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Posture Monitor')
    parser.add_argument('--threshold', type=float, default=3.0, help='Angle deviation threshold (degrees). Triggers if abs(angle) > threshold.')
    parser.add_argument('--alpha', type=float, default=0.1, help='Smoothing factor (0.01-1.0). smaller = smoother.')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID')
    args = parser.parse_args()

    monitor = PostureMonitor(threshold_angle=args.threshold, camera_id=args.camera)
    # Update state from args
    monitor.alpha = args.alpha
    monitor.run()
