import cv2
import mediapipe as mp
import numpy as np
import time

class PostureMonitor:
    def __init__(self, threshold_angle=15.0, camera_id=0):
        # Threshold is now Pitch angle in degrees (e.g., > 15 degrees is looking down)
        self.threshold_angle = threshold_angle 
        self.camera_id = camera_id
        
        # MediaPipe Setup
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # State
        self.down_count = 0
        self.is_down = False
        self.prev_time = 0
        
        # Smoothing (Exponential Moving Average)
        self.smooth_pitch = 0
        self.alpha = args.alpha if 'args' in globals() else 0.2
        
        # 3D Model Points (Standard Generic Face Model)
        # Coordinates in arbitrary units, centered roughly at the head
        self.face_3d = np.array([
            [0.0, 0.0, 0.0],            # Nose tip (Landmark 1)
            [0.0, -330.0, -65.0],       # Chin (Landmark 152)
            [-225.0, 170.0, -135.0],    # Left eye left corner (Landmark 33)
            [225.0, 170.0, -135.0],     # Right eye right corner (Landmark 263)
            [-150.0, -150.0, -125.0],   # Left Mouth corner (Landmark 61)
            [150.0, -150.0, -125.0]     # Right Mouth corner (Landmark 291)
        ], dtype=np.float64)

        # Corresponding MediaPipe Indices
        self.face_2d_indices = [1, 152, 33, 263, 61, 291]

    def get_head_pose(self, face_landmarks, img_w, img_h):
        face_2d = []
        for idx in self.face_2d_indices:
            lm = face_landmarks.landmark[idx]
            x, y = int(lm.x * img_w), int(lm.y * img_h)
            face_2d.append([x, y])
        
        face_2d = np.array(face_2d, dtype=np.float64)

        # Camera Matrix (Approximation)
        focal_length = 1 * img_w
        cam_matrix = np.array([
            [focal_length, 0, img_h / 2],
            [0, focal_length, img_w / 2],
            [0, 0, 1]
        ])
        
        # Distance Matrix (Assuming no lens distortion for simplicity)
        dist_matrix = np.zeros((4, 1), dtype=np.float64)

        # Solve PnP
        success, rot_vec, trans_vec = cv2.solvePnP(self.face_3d, face_2d, cam_matrix, dist_matrix)

        if not success:
            return None, None

        # Convert Rotation Vector to Rotation Matrix
        rmat, jac = cv2.Rodrigues(rot_vec)

        # Calculate Euler Angles
        # Project a 3D point to get pitch/yaw/roll roughly or use matrix decomposition
        # Standard decomposition for head pose:
        # Pitch: Rotation around X-axis (Looking up/down)
        # Yaw: Rotation around Y-axis (Looking left/right)
        # Roll: Rotation around Z-axis (Tilt left/right)
        
        angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

        # Angles are in degrees
        pitch = angles[0] * 360
        yaw = angles[1] * 360
        roll = angles[2] * 360
        
        return pitch, (rot_vec, trans_vec, cam_matrix, dist_matrix, face_2d[0])

    def process_frame(self, frame, face_mesh):
        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(img_rgb)
        
        current_pitch = None
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Draw the 6 anchor points used for PnP calculation
            for idx in self.face_2d_indices:
                lm = face_landmarks.landmark[idx]
                pt_x, pt_y = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (pt_x, pt_y), 3, (255, 255, 0), -1) # Cyan dots

            # Get Head Pose
            pitch, debug_info = self.get_head_pose(face_landmarks, w, h)
            
            if pitch is not None:
                # Smoothing
                if self.smooth_pitch == 0:
                    self.smooth_pitch = pitch
                else:
                    self.smooth_pitch = self.alpha * pitch + (1 - self.alpha) * self.smooth_pitch
                
                current_pitch = self.smooth_pitch
                
                # Visuals: Draw Nose Direction or Axis
                rot_vec, trans_vec, cam_matrix, dist_matrix, nose_2d = debug_info
                
                # Project axis points to visualize
                # X-axis (Pitch) - Red, Y-axis (Yaw) - Green, Z-axis (Forward) - Blue
                axis_length = 50
                axis_points_3d = np.array([
                    [axis_length, 0, 0],
                    [0, axis_length, 0],
                    [0, 0, axis_length] 
                ], dtype=np.float64)
                
                axis_points_2d, _ = cv2.projectPoints(axis_points_3d, rot_vec, trans_vec, cam_matrix, dist_matrix)
                
                p_nose = (int(nose_2d[0]), int(nose_2d[1]))
                p_x = (int(axis_points_2d[0][0][0]), int(axis_points_2d[0][0][1])) # Pitch Axis
                p_y = (int(axis_points_2d[1][0][0]), int(axis_points_2d[1][0][1])) # Yaw Axis
                
                # Draw visual axes
                cv2.line(frame, p_nose, p_x, (0, 0, 255), 2) # Red: Pitch movement axis
                cv2.line(frame, p_nose, p_y, (0, 255, 0), 2) # Green: Yaw movement axis

                # Logic: Check Down (Pitch)
                # Usually Pitch > Threshold means looking down. 
                # Note: Depending on coordinate system, looking down might be positive or negative.
                # In this RQDecomp setup, Looking DOWN usually increases Pitch (Positive).
                
                is_posture_bad = False
                if current_pitch > self.threshold_angle:
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
                cv2.putText(frame, f"Pitch: {current_pitch:.1f} deg", (50, 150),
                            cv2.FONT_HERSHEY_PLAIN, 2, color, 2)
                cv2.putText(frame, f"Limit: > {self.threshold_angle}", (w - 250, 80),
                            cv2.FONT_HERSHEY_PLAIN, 1.5, (200, 200, 200), 2)

        return frame

    def run(self):
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        print("Starting 3D Posture Monitor...")
        print(f"Pitch Threshold: {self.threshold_angle} degrees (Positive = Down)")
        
        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        ) as face_mesh:
            
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    continue

                frame = cv2.flip(frame, 1) # Mirror view
                frame = self.process_frame(frame, face_mesh)

                curr_time = time.time()
                fps = 1 / (curr_time - self.prev_time) if (curr_time - self.prev_time) > 0 else 0
                self.prev_time = curr_time
                
                h, w, _ = frame.shape
                cv2.putText(frame, f"FPS: {int(fps)}", (w - 150, 50), 
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                cv2.putText(frame, f"Count: {self.down_count}", (50, 100),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

                cv2.imshow('3D Posture Monitor (PnP)', frame)

                if cv2.waitKey(5) & 0xFF == 27:
                    break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    import argpars
    parser = argparse.ArgumentParser(description='3D Posture Monitor')
    parser.add_argument('--threshold', type=float, default=15.0, help='Pitch threshold degrees (Default 15).')
    parser.add_argument('--alpha', type=float, default=0.2, help='Smoothing factor.')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID')
    args = parser.parse_args()

    monitor = PostureMonitor(threshold_angle=args.threshold, camera_id=args.camera)
    monitor.alpha = args.alpha
    monitor.run()