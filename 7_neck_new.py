"""
CTAR Posture Monitor - Pygame Version
使用 MediaPipe Face Mesh + Pygame 顯示
包含校準、Yaw 過濾和基於鼻子-下巴距離的低頭偵測

Optimization Changes:
1. Threaded Webcam Capture
2. Lower resolution for inference (640x360)
3. Disabled refine_landmarks (faster, iris not needed)
"""

import cv2
import mediapipe as mp
import numpy as np
import pygame
import time
import math
from threading import Thread

# ==================== 設定 ====================
CAMERA_ID = 0
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
INFERENCE_WIDTH = 640  # 推理用寬度
INFERENCE_HEIGHT = 360 # 推理用高度
THRESHOLD_RATIO = 0.20  # 低頭偵測閾值 (20%)
YAW_TOLERANCE = 0.10     # 轉頭容忍度 (10%)
CALIBRATION_DURATION = 3  # 校準時間 (秒)

# Landmark 索引
NOSE_TIP = 1
CHIN = 152
LEFT_EYE_OUTER = 263
RIGHT_EYE_OUTER = 33

# ==================== 類別定義 ====================
class WebcamStream:
    """多執行緒攝影機擷取"""
    def __init__(self, src=0, width=1280, height=720):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1) # 減少延遲
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update, args=()).start()
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

# ==================== 初始化 ====================
pygame.init()
pygame.display.set_caption("CTAR Posture Monitor (Optimized)")
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 32)
font_tiny = pygame.font.Font(None, 24)

# MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=False, # 優化：關閉虹膜偵測以加速
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 啟動攝影機執行緒
cap = WebcamStream(src=CAMERA_ID, width=WINDOW_WIDTH, height=WINDOW_HEIGHT).start()
time.sleep(1.0) # 等待攝影機暖機

# ==================== 狀態變數 ====================
is_calibrated = False
calibration_start_time = None
calibration_samples_eye = []
calibration_samples_nose_chin = []
baseline_eye_distance = 0
baseline_nose_chin_distance = 0

down_count = 0
is_down = False
is_turning = False
current_ratio = 0.0
fps = 0
prev_time = time.time()

# ==================== 輔助函數 ====================
def calculate_distance(p1, p2):
    """計算兩點間的歐幾里得距離"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def get_metrics(face_landmarks, w, h):
    """從臉部地標取得眼距和鼻子-下巴距離"""
    nose = face_landmarks.landmark[NOSE_TIP]
    chin = face_landmarks.landmark[CHIN]
    left_eye = face_landmarks.landmark[LEFT_EYE_OUTER]
    right_eye = face_landmarks.landmark[RIGHT_EYE_OUTER]
    
    # 像素位置 (Mapping back to original resolution)
    nose_pt = (nose.x * w, nose.y * h)
    chin_pt = (chin.x * w, chin.y * h)
    left_eye_pt = (left_eye.x * w, left_eye.y * h)
    right_eye_pt = (right_eye.x * w, right_eye.y * h)
    
    # 使用水平眼距（只看 X 軸）來偵測轉頭
    eye_horizontal_distance = abs(right_eye_pt[0] - left_eye_pt[0])
    nose_chin_distance = calculate_distance(nose_pt, chin_pt)
    
    return {
        "eye_distance": eye_horizontal_distance,
        "nose_chin_distance": nose_chin_distance,
        "points": (nose_pt, chin_pt, left_eye_pt, right_eye_pt)
    }

def draw_text(text, x, y, color=(255, 255, 255), font=None):
    """在 pygame 上繪製文字"""
    if font is None:
        font = font_medium
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def cv2_to_pygame(frame):
    """將 OpenCV 影像轉換為 Pygame surface"""
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    frame = np.flipud(frame)
    return pygame.surfarray.make_surface(frame)

# ==================== 主迴圈 ====================
running = True
while running:
    # 事件處理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:  # 按 R 重新校準
                is_calibrated = False
                calibration_start_time = None
                calibration_samples_eye = []
                calibration_samples_nose_chin = []
    
    # 讀取影像 (從 Thread)
    frame = cap.read()
    if frame is None:
        continue
    
    # 鏡像翻轉
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # 優化：縮小影像進行推理
    frame_small = cv2.resize(frame, (INFERENCE_WIDTH, INFERENCE_HEIGHT))
    rgb_frame_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
    
    # 推理
    results = face_mesh.process(rgb_frame_small)
    
    # 計算 FPS
    curr_time = time.time()
    fps = int(1 / (curr_time - prev_time)) if (curr_time - prev_time) > 0 else 0
    prev_time = curr_time
    
    face_detected = False
    
    if results.multi_face_landmarks:
        face_landmarks = results.multi_face_landmarks[0]
        face_detected = True
        
        # metrics 使用原始 w, h 計算，因為 landmarks 是正規化的 (0.0 - 1.0)
        metrics = get_metrics(face_landmarks, w, h)
        
        nose_pt, chin_pt, left_eye_pt, right_eye_pt = metrics["points"]
        
        # 繪製臉部地標 (畫在原始高解析度 frame 上)
        cv2.circle(frame, (int(nose_pt[0]), int(nose_pt[1])), 5, (0, 255, 0), -1)
        cv2.circle(frame, (int(chin_pt[0]), int(chin_pt[1])), 5, (0, 0, 255), -1)
        cv2.circle(frame, (int(left_eye_pt[0]), int(left_eye_pt[1])), 5, (255, 255, 0), -1)
        cv2.circle(frame, (int(right_eye_pt[0]), int(right_eye_pt[1])), 5, (255, 255, 0), -1)
        cv2.line(frame, (int(nose_pt[0]), int(nose_pt[1])), (int(chin_pt[0]), int(chin_pt[1])), (255, 0, 255), 2)
        cv2.line(frame, (int(left_eye_pt[0]), int(left_eye_pt[1])), (int(right_eye_pt[0]), int(right_eye_pt[1])), (0, 255, 255), 2)
        
        # ================== 校準階段 ==================
        if not is_calibrated:
            if calibration_start_time is None:
                calibration_start_time = time.time()
            
            elapsed = time.time() - calibration_start_time
            progress = min(elapsed / CALIBRATION_DURATION, 1.0)
            
            # 收集樣本
            calibration_samples_eye.append(metrics["eye_distance"])
            calibration_samples_nose_chin.append(metrics["nose_chin_distance"])
            
            if elapsed >= CALIBRATION_DURATION:
                # 校準完成
                baseline_eye_distance = np.median(calibration_samples_eye)
                baseline_nose_chin_distance = np.median(calibration_samples_nose_chin)
                if baseline_eye_distance == 0: baseline_eye_distance = 1 # 防止除以零
                if baseline_nose_chin_distance == 0: baseline_nose_chin_distance = 1
                
                is_calibrated = True
                print(f"校準完成: 眼距基準={baseline_eye_distance:.1f}, 鼻下巴距基準={baseline_nose_chin_distance:.1f}")
            else:
                # 繪製校準進度條
                bar_width = 400
                bar_height = 30
                bar_x = (w - bar_width) // 2
                bar_y = h // 2 + 50
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + bar_height), (0, 200, 100), -1)
                cv2.putText(frame, f"Calibrating... {int(progress * 100)}%", (bar_x, bar_y - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, "Look straight ahead", (bar_x, bar_y + bar_height + 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        
        # ================== 姿態偵測 ==================
        else:
            eye_distance = metrics["eye_distance"]
            nose_chin_distance = metrics["nose_chin_distance"]
            
            # 計算相對變化
            eye_deviation = abs(eye_distance - baseline_eye_distance) / baseline_eye_distance
            nose_chin_ratio = (nose_chin_distance - baseline_nose_chin_distance) / baseline_nose_chin_distance
            current_ratio = nose_chin_ratio * 100  # 轉換為百分比
            
            # 轉頭過濾
            if eye_deviation > YAW_TOLERANCE:
                is_turning = True
            else:
                is_turning = False
                
                # 低頭偵測 (鼻子-下巴距離縮短代表低頭)
                if nose_chin_ratio < -THRESHOLD_RATIO:
                    if not is_down:
                        down_count += 1
                        is_down = True
                elif nose_chin_ratio > -(THRESHOLD_RATIO * 0.6):  # Hysteresis
                    is_down = False
    
    # ==================== Pygame 繪製 ====================
    # 轉換並顯示影像
    pygame_frame = cv2_to_pygame(frame)
    screen.blit(pygame_frame, (0, 0))
    
    # 繪製 HUD
    # 左上角 - 狀態
    if is_calibrated:
        if is_turning:
            draw_text("TURNING - Detection Paused", 20, 20, (255, 200, 0), font_medium)
        elif is_down:
            draw_text("HEAD DOWN!", 20, 20, (255, 50, 50), font_large)
        else:
            draw_text("Posture OK", 20, 20, (50, 255, 100), font_medium)
    else:
        draw_text("Calibrating...", 20, 20, (150, 150, 255), font_medium)
    
    # 右上角 - 數據
    draw_text(f"FPS: {fps}", WINDOW_WIDTH - 150, 20, (200, 200, 200), font_small)
    draw_text(f"RES: {INFERENCE_WIDTH}x{INFERENCE_HEIGHT}", WINDOW_WIDTH - 150, 50, (150, 150, 150), font_tiny)
    
    # 右側 - 統計
    info_x = WINDOW_WIDTH - 300
    draw_text(f"Down Count: {down_count}", info_x, 80, (255, 255, 255), font_medium)
    
    if is_calibrated:
        ratio_color = (255, 100, 100) if current_ratio < -THRESHOLD_RATIO * 100 else (100, 255, 100)
        draw_text(f"Ratio: {current_ratio:+.1f}%", info_x, 130, ratio_color, font_small)
        
        # 繪製比例條
        bar_width = 200
        bar_height = 20
        bar_x = info_x
        bar_y = 170
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # 中間線
        pygame.draw.line(screen, (255, 255, 255), (bar_x + bar_width // 2, bar_y), 
                        (bar_x + bar_width // 2, bar_y + bar_height), 2)
        
        # 當前位置
        indicator_pos = int(bar_x + bar_width // 2 - (current_ratio / 50) * (bar_width // 2))
        indicator_pos = max(bar_x, min(bar_x + bar_width, indicator_pos))
        pygame.draw.circle(screen, ratio_color, (indicator_pos, bar_y + bar_height // 2), 8)
    
    # 底部 - 控制提示
    draw_text("ESC: Exit | R: Recalibrate", 20, WINDOW_HEIGHT - 40, (150, 150, 150), font_small)
    
    # 更新顯示
    pygame.display.flip()
    clock.tick(60)

# ==================== 清理 ====================
cap.stop()
face_mesh.close()
pygame.quit()
print(f"\n總共低頭次數: {down_count}")
