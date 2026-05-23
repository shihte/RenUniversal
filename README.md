# 🚀 CTAR：次世代分散式智慧姿態監控代理系統 (Next-Gen AI Posture Agent)

[![Python](https://img.shields.io/badge/Python-3.8--3.11-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-teal.svg?style=for-the-badge&logo=google)](https://mediapipe.dev/)
[![Architecture](https://img.shields.io/badge/Architecture-Agentic--Modular-orange.svg?style=for-the-badge)](https://github.com/shihte/CTAR)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**CTAR (Cybernetic Tracking & Analysis Repository)** 是一個基於電腦視覺邊緣運算（Edge Computing）與多代理人（Agent）架構的生理姿態回饋與即時監控系統。系統摒棄了傳統的硬編碼、線性判定邏輯，採用模組化插件架構（Agent Skills）、強型別幾何特徵交換協議以及雙執行緒非同步流水線，可在低耗能邊緣設備上實現高精度的三維頭部與軀幹姿態估算。

---

## 🔬 核心技術與演算法設計

### 1. 影像擷取線程與硬體抽象 (VideoCaptureService)
*   **非同步雙緩衝 (Asymmetric Double Buffering)**：`VideoCaptureSkill` 透過獨立讀取線程運行，限制 OpenCV 內部緩衝區，配合 `threading.Lock` 確保 30Hz 串流讀取無 I/O 阻塞，降低延遲至微秒級。
*   **自癒重連 (Self-Healing Recovery)**：內建指數退避（Exponential Backoff）與故障狀態檢測，當相機斷開或 USB 訊號中斷時，能自動釋放資源並於背景嘗試重新連接。

### 2. 三維姿態幾何評估演算法 (Feature Vector Mathematics)
系統利用 MediaPipe Landmark 模型提取的特徵座標進行三維空间向量投影，以量化人體生理姿態：

*   **低頭比例 (Nose-Chin Ratio - 俯仰角估算)**：
    評估頭部前傾程度，藉由鼻尖（Nose, Landmark 4）與下巴（Chin, Landmark 152）在投影面上的垂直長度比率變化估算：
    $$\text{Ratio} = \frac{(y_{\text{chin}} - y_{\text{nose}}) - d_{\text{baseline}}}{d_{\text{baseline}}}$$
    當頭部俯仰角增加（低頭），該比率將呈現負值偏離。

*   **頭部偏轉比 (Yaw Deviation - 偏航角估算)**：
    計算左右眼角外側（Landmarks 33, 263）相對於鼻尖的水平間距比率，以此估算左右擺頭角度：
    $$\text{Yaw} = \frac{x_{\text{nose}} - x_{\text{left\_eye}}}{x_{\text{right\_eye}} - x_{\text{left\_eye}}} - 0.5$$

*   **肩部傾斜度 (Shoulder Slope - 側傾角估算)**：
    計算左右肩峰點（Pose Landmarks 11, 12）連線的斜率：
    $$\text{Slope} = \frac{y_{\text{right\_shoulder}} - y_{\text{left\_shoulder}}}{x_{\text{right\_shoulder}} - x_{\text{left\_shoulder}}}$$

*   **磁滯抗噪濾波器 (Hysteresis Filter)**：
    為了防止臨界值狀態下的狀態震盪，系統對狀態變更實作了磁滯區間限制（邊界補償），降低高頻環境抖動引起的誤報率。

### 3. 動態插件規則引擎 (Action Judgment Engine)
*   **動態插件發現 (Dynamic Plugin Discovery)**：`ActionEngine` 會於運行時反射式掃描 `skills/` 底下的所有動作判斷包，加載其 `config.json` 設定，無需重寫編譯即可擴充新型態的姿態判定。
*   **強型別 I/O 驗證**：利用 Pydantic 2.0 進行資料格式驗證，保證所有 Skills 在傳遞與接收姿態變數時的結構一致性。

---

## 🛠 開發先前條件 (Prerequisites)

在部署與運行本系統前，請確保您的主機環境符合以下規範：

*   **作業系統**：macOS (12.0+), Linux (Ubuntu 20.04+), Windows 10/11
*   **Python 版本**：**Python 3.8 至 Python 3.11** (因 MediaPipe 原生編譯二進制檔限制，不支援更高或更低版本)
*   **硬體要求**：
    *   具備 UVC 協定的 USB 外接相機 或 整合式 Webcam。
    *   **行動裝置協同 (Mobile Co-processor)**：無需額外下載 App，透過行動裝置瀏覽器掃描 QR Code 即可建立雙向 WebSocket/HTTP 視訊流通道，支援與主機鏡頭構成**雙鏡頭聯合偵測模式 (Dual-Camera Mode)**。
*   **網路要求**：若使用行動裝置協同，需確保裝置與主機於同一區域網路，或透過系統內建的遠端公網穿透技術（支援跨網段/行動網路）。
*   **系統套件** (Linux 用戶)：
    ```bash
    sudo apt-get update && sudo apt-get install -y python3-dev build-essential libgl1-mesa-glx
    ```

---

## 🚀 快速部署引導 (Cloning & Setup)

### 1. 複製專案庫
```bash
git clone https://github.com/shihte/CTAR.git
cd CTAR
```

### 2. 環境初始化與依賴安裝
系統內建自動化語法檢查與環境配置。執行以下命令，Makefile 將自動偵測當前作業系統上的相容 Python 版本（3.8 - 3.11），建立虛擬環境，升級 pip，並安裝所有核心依賴：
```bash
make setup
```

### 3. 運行系統

*   **前台偵錯模式**：
    ```bash
    make run
    ```
*   **背景守護進程模式** (將 PID 保存至 `.agent.pid`，日誌輸出至 `agent.log`)：
    ```bash
    make start
    ```
*   **終止背景服務**：
    ```bash
    make stop
    ```

### 4. 架構合規性測試
執行單元測試以確保 Pydantic 結構體與 SharedState 模型狀態讀寫符合系統預期：
```bash
make test
```

---

## 📂 模組目錄架構與映射

```text
.
├── Makefile                # 統一入口編排（含 Python 版本相容性自適應檢查）
├── backend/                # 偵測代理後端核心
│   ├── core/               # 核心資料處理流水線與狀態管理
│   │   ├── action_engine.py# 動態規則匹配與熱載入引擎
│   │   ├── pipeline.py     # 影像特徵提取、座標幾何轉換與 MediaPipe 驅動
│   │   ├── schema.py       # Pydantic 數據模型與強型別 I/O 驗證
│   │   └── state.py        # 線程安全共用狀態隔離器
│   ├── services/           # 基礎硬體控制與校準引導
│   │   ├── video_capture/  # 支援 USB/行動端外接攝像頭自癒串流模組
│   │   └── calibration_wizard/ # 控制反轉 (IoC) 平均採樣校準演算法
│   └── stream_server.py    # Flask RESTful API & MJPEG 視訊串流伺服器
├── skills/                 # 動態自定義動作判斷包目錄 (AJP)
│   ├── slouch/             # 駝背判定包
│   ├── sway/               # 左右搖晃判定包
│   └── lean/               # 前傾判定包
├── docs/                   # 系統設計決策與詳細規格文件
└── web/                    # 靜態 HTML5 / CSS3 / VanillaJS 高效戰情儀表板
```

---

## 🛡 系統技術指標

*   **三維面部網格**：468 點面部幾何拓撲點
*   **身體姿態追蹤**：33 點全身骨架關節點
*   **採樣頻率**：30Hz 恆定硬體捕獲與分析頻率
*   **通訊協議**：MJPEG (影像) + RESTful / JSON (狀態與參數設定)
*   **儲存持久化**：JSON 本地輕量化狀態紀錄器 (`preferences.json`)

### 新增功能 (Latest Updates)
*   **Dual-Camera Mobile WiFi Streaming**: 支援同時接收電腦預設鏡頭 (Local Camera) 與手機網路串流 (Mobile WiFi Stream)，並透過 `cv2.hconcat` 於邊緣端自動進行畫面縫合 (Stitching)，達到一鏡負責臉部特徵 (FaceMesh)、一鏡負責身體骨架 (Pose) 的進階雙相機評估架構。
*   **UI 穩定性優化**: 修復前端相機選擇器 (Camera Sources) 的狀態覆寫問題，確保勾選操作流暢並自動連動校準程序。
