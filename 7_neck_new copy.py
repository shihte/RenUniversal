import cv2
import mediapipe as mp
import math

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic()

cv2.namedWindow('Webcam',cv2.WINDOW_NORMAL)
cap = cv2.VideoCapture(0)

# ---- 計數器變數 ----
down_count = 0
is_down = False  # 狀態旗標：是否正在低頭

while cap.isOpened():
    ret, frame = cap.read()
    frame = cv2.flip(frame,1)
    imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = holistic.process(imgRGB)

    if results.face_landmarks:
        h, w, _ = frame.shape
        # landmark index: 152 (下巴), 10 (前額)
        x_chin, y_chin = int(results.face_landmarks.landmark[152].x * w), int(results.face_landmarks.landmark[152].y * h)
        x_fore, y_fore = int(results.face_landmarks.landmark[10].x * w), int(results.face_landmarks.landmark[10].y * h)

        # 向量 chin → forehead
        vx = x_fore - x_chin
        vy = y_fore - y_chin

        # 算和垂直方向(0, -1)的角度
        head_angle = math.degrees(math.atan2(vx, -vy))
        head_angle = round(head_angle,1)

        # 畫點與線
        cv2.circle(frame,(x_chin,y_chin),5,(0,0,255),-1)
        cv2.circle(frame,(x_fore,y_fore),5,(0,255,0),-1)
        cv2.line(frame,(x_chin,y_chin),(x_fore,y_fore),(255,0,0),2)

        # 顯示角度
        cv2.putText(frame, f"Head angle: {head_angle} deg", (50,150),
                    cv2.FONT_HERSHEY_PLAIN, 2, (0,255,255), 2)

        # ---- 判斷是否低頭 ----
        if head_angle < -20:  # 閾值可自行調整
            # cv2.putText(frame, "Looking DOWN", (50,200),
            #             cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
            if not is_down:  # 剛剛開始低頭
                down_count += 1
                is_down = True
        elif head_angle > 17:  # 閾值可自行調整
            # cv2.putText(frame, "Looking DOWN", (50,200),
            #             cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
            if not is_down:  # 剛剛開始低頭
                down_count += 1
                is_down = True
        elif head_angle > -10 and head_angle < 10 and is_down == True:
            is_down = False  # 回到正常狀態，允許下次再計數
        
        

    # 顯示計數器
    cv2.putText(frame, f"Down Count: {down_count}", (50,250),
                cv2.FONT_HERSHEY_PLAIN, 3, (0,255,0), 3)

    # 繪製臉部骨架
    mp_drawing.draw_landmarks(frame, results.face_landmarks,
                              mp_holistic.FACEMESH_CONTOURS,
                              landmark_drawing_spec=None,
                              connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style())

    cv2.imshow('Webcam',frame)
    key = cv2.waitKey(1)
    if key==27: # ESC
        break

cap.release()
cv2.destroyAllWindows()
