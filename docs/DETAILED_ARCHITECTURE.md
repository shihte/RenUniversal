# CTAR 代理架構精確技術規範 (DETAILED ARCHITECTURE)

本文件提供 CTAR 專案的核心邏輯說明，精確對應至程式碼行號，旨在為開發者提供透明的技術導覽。

## 1. 核心流水線 (Agent Pipeline)
**檔案位置**: `backend/core/pipeline.py`

| 行號範圍 | 功能模組 | 設計模式與邏輯說明 |
| :--- | :--- | :--- |
| **L20-L57** | **初始化 (Lifecycle)** | 建立並啟動 `VideoCaptureSkill` [L38]；初始化 Pydantic 配置與 MediaPipe 模型 [L43-L50]。 |
| **L59-L87** | **特徵提取 (Feature Extraction)** | **封裝邏輯**: 透過 `_extract_physical_features` 將 Mediapipe 的歸一化座標轉換為像素距離 [L81-L85]。 |
| **L98-L101** | **擷取環節 (Capture)** | 呼叫 `VideoCaptureSkill` 工具包裝器讀取影格。 |
| **L113-L129** | **校準引導 (Inversion)** | **反轉模式**: 若未校準，將特徵送入 `CalibrationWizardSkill` [L119] 並寫回進度至狀態機。 |
| **L131-L147** | **姿勢審查 (Reviewer)** | **審查模式**: 調用 `PostureReviewerSkill` 進行邏輯評估，並實作可觀測性 (Observability) 寫回檢測數據 [L143-L146]。 |

---

## 2. 影像擷取技能 (Video Capture Skill)
**檔案位置**: `skills/video_capture/logic.py`

| 行號範圍 | 功能模組 | 設計模式與邏輯說明 |
| :--- | :--- | :--- |
| **L20-L40** | **硬體抽象 (Abstraction)** | **Tool Wrapper**: 封裝 OpenCV `VideoCapture` 並配置緩衝區大小 [L38] 以減少延遲。 |
| **L49-L74** | **防禦性重連 (Resilience)** | **故障恢復**: 實作指數退避算法 [L68]；當擷取失敗時釋放資源並定時重連 [L58-L65]。 |
| **L84-L93** | **線程安全讀取** | 使用 `threading.Lock` 保護影格資源，確保 MJPEG 串流與分析線程不衝突。 |

---

## 3. 姿勢審查技能 (Posture Reviewer Skill)
**檔案位置**: `skills/posture_reviewer/logic.py`

| 行號範圍 | 功能模組 | 設計模式與邏輯說明 |
| :--- | :--- | :--- |
| **L41-L86** | **核心評估 (Evaluation)** | **Reviewer**: 接收特徵數據進行物理判定。 |
| **L70-L71** | **轉頭過濾 (Yaw Filter)** | 計算當前眼距與基準的偏差比率，若超出 `yaw_tolerance` 則標註為 `is_turning`。 |
| **L79-L86** | **磁滯效應 (Hysteresis)** | **穩定性優化**: 實作 `+0.05` 的緩衝區 [L83]，防止使用者在閾值邊界產生的頻繁告警切換。 |

---

## 4. 校準精靈技能 (Calibration Wizard Skill)
**檔案位置**: `skills/calibration_wizard/logic.py`

| 行號範圍 | 功能模組 | 設計模式與邏輯說明 |
| :--- | :--- | :--- |
| **L40-L86** | **交互驅動 (Interaction)** | **Inversion**: 代理進入「等待狀態」，收集樣本而非執行動作。 |
| **L68-L69** | **數據採樣 (Sampling)** | 在校準期間持續將影像特徵存入緩衝列表，用於後續計算平均值。 |
| **L76-L78** | **基準計算 (Baseline)** | 採樣結束後透過 `np.mean` 計算基準數值，並輸出為 `CalibrationResult`。 |

---

## 技術決策記錄 (ADR)
1.  **為什麼使用 Pydantic?**
    - 確保 Skill 與 Pipeline 之間的 I/O 是強型別且自說明的，符合 Google ADK 的 Typed I/O 原則。
2.  **為什麼採用 MJPEG 串流?**
    - 提供低延遲的 Web 即時預覽，且無須複雜的 WebRTC 握手。
3.  **為什麼設計 Inversion 模式?**
    - 使用者環境不同（攝像頭角度、距離），固定閾值無法準確檢測。透過 Inversion 獲取個人化基準是唯一的可靠方案。
