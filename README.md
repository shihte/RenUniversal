# 🚀 RenUniversal：智慧下巴內縮抗阻力復健監控系統 (AI Chin-tuck Against Resistance Monitor)

[![Python](https://img.shields.io/badge/Python-3.8--3.11-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-teal.svg?style=for-the-badge&logo=google)](https://mediapipe.dev/)
[![Architecture](https://img.shields.io/badge/Architecture-Agentic--Modular-orange.svg?style=for-the-badge)](https://github.com/shihte/RenUniversal)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**RenUniversal（Chin-tuck Against Resistance，下巴內縮抗阻力運動）** 是一種專業的吞嚥復健訓練。透過對抗阻力，能有效強化舌骨上肌群，改善喉部上提不足及上食道括約肌運動，幫助吞嚥障礙患者恢復由口進食。

本專案是一個基於電腦視覺邊緣運算（Edge Computing）的 **AI 生理姿態回饋與即時監控系統**，專為輔助患者在進行 RenUniversal 訓練（如夾球等長與等動運動）時，提供正確的頭部、下巴及軀幹姿態即時評估。

系統摒棄了傳統的硬編碼與線性判定邏輯，導入了高度模組化與高通用性的 **多代理人技能架構（Agent Skills Architecture）**，使臨床人員或開發者能輕易抽換、擴充不同的姿態判定邏輯。

---

## 🔬 核心技術與模組化通用架構 (Modularity & Generalizability)

### 1. 動態插件規則引擎 (Action & Event Engine)
本系統的極致通用性建立在其**「技能模組化 (Skills Modularity)」**與**「事件分離 (Event Pipeline)」**設計上：
*   **熱插拔技能 (Hot-Pluggable Agent Skills)**：`ActionEngine` 於運行時會動態反射式掃描 `skills/` 目錄下的判定包（例如：低頭 `lean`、駝背 `slouch`、轉頭 `turn` 等）。開發者只需繼承統一的 `SkillTemplate` 介面新增目錄，無需重寫編譯核心框架，即可為系統擴充全新的身體動作特徵判定。
*   **高階事件組合 (Event Engine)**：底層偵測到的單一動作特徵（如：低頭達標、無代償轉頭等），會被傳遞給 Event Engine 進行高階邏輯判定。這種底層「特徵 (Skills)」與高層「事件 (Events)」解耦的設計，讓系統不再侷限於 RenUniversal，可以輕易泛化 (Generalize) 應用於各類復健運動評估。

### 2. 三維姿態幾何評估演算法 (Feature Vector Mathematics)
系統利用 MediaPipe Landmark 提取特徵座標進行三維向量投影，量化人體生理姿態（例如計算鼻尖與下巴的垂直比例變化來判定低頭角度，或是肩峰點連線斜率以偵測軀幹代償偏移）。同時內建**磁滯抗噪濾波器 (Hysteresis Filter)**，防止臨界狀態震盪，大幅降低高頻環境抖動引起的誤報。

### 3. 影像擷取線程與硬體抽象 (VideoCaptureService)

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
git clone https://github.com/shihte/RenUniversal.git
cd RenUniversal
```

### 2. 環境初始化與依賴安裝
系統內建自動化語法檢查與環境配置。執行以下命令，Makefile 將自動偵測當前作業系統上的相容 Python 版本（3.8 - 3.11），建立虛擬環境，升級 pip，並安裝所有核心依賴：
```bash
make setup
```

### 3. 運行系統

*   **Mac / Linux 用戶 (使用 Makefile)**：
    *   前台偵錯模式：`make run`
    *   背景守護進程模式：`make start`（日誌將輸出至 `agent.log`）
    *   終止背景服務：`make stop`
    *   架構合規性測試：`make test`

*   **Windows 用戶 (使用 renuniversal.bat)**：
    Windows 原生環境對 Makefile 支援較差，請改用專屬的 `renuniversal.bat` 腳本：
    1.  初始化環境與安裝：在命令提示字元 (cmd) 執行 `renuniversal.bat setup`
    2.  啟動伺服器：執行 `renuniversal.bat run`
    3.  執行測試：執行 `renuniversal.bat test`
    4.  清除暫存：執行 `renuniversal.bat clean`

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
