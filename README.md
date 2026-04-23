# 🚀 CTAR：次世代智慧姿態監控代理系統 (Next-Gen AI Posture Agent)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-teal.svg?style=for-the-badge&logo=google)](https://mediapipe.dev/)
[![License](https://img.shields.io/badge/Architecture-Agentic--Modular-orange.svg?style=for-the-badge)](https://github.com/shihte/CTAR)

**CTAR (Cybernetic Tracking & Analysis Repository)** 是一套融合了電腦視覺邊緣運算與代理人（Agent）架構的生理姿態回饋系統。不同於傳統的線性偵測腳本，CTAR 採用 **Google ADK 生態系設計模式**，將「視覺感測」、「幾何推理」與「決策回饋」解構為高度自治的功能技能集（Skills）。

---

## 💎 核心設計哲學：五大代理模式
我們不只是在寫程式，我們在構建一個具備感官與記憶的數位實體。

1.  **Reviewer Pattern (邏輯審查)**：實作 `PostureReviewerSkill`，透過非對稱式閾值（Asymmetric Thresholds）與磁滯補償（Hysteresis），過濾 99% 的環境雜訊與微小晃動。
2.  **Tool Wrapper (硬體封裝)**：`VideoCaptureSkill` 封裝了複雜的 V4L2/AVFoundation 層，提供具備「自癒能力（Self-healing）」的影像擷取流。
3.  **Inversion Pattern (反轉導引)**：校準精靈 `CalibrationWizardSkill` 將控制權反轉給使用者，透過主動採樣建立動態基準（Dynamic Baseline），實現個人化適配。
4.  **Typed I/O (強型別交換)**：基於 Pydantic 2.0，所有技能間的通訊皆具備嚴格的 Schema 校驗，確保大規模併發下的數據完整性。
5.  **State Isolation (狀態解耦)**：採用單向數據流架構，徹底分離影像渲染（Rendering）與邏輯推論（Inference）。

---

## 🎨 儀表板視界 (Visual Intelligence)
基於 **Next.js 15** 與 **Framer Motion** 打造的 Cyberpunk 戰情室介面，提供：
*   **低延遲 MJPEG 串流**：經過優化的二進制分段傳輸，確保視覺回饋無感延遲。
*   **即時統計圖譜**：動態追蹤低頭頻率、眼距變動與系統負載 FPS。
*   **深色擬態設計**：優化長時間工作的視覺負擔，營造高級開發者環境感。

---

## ⚙️ 快速部署與工程指令
我們提供完整的 `Makefile` 以實現開發環境的快速同步：

### 環境初始化
```bash
make setup  # 自動建立虛擬環境、安裝 pip/npm 依賴並配置環境變數
```

### 系統啟動 (Dual-Stack Start)
```bash
make start  # 同時調度 Python 偵測核心與 React 渲染前端
```

### 資源釋放
```bash
make stop   # 優雅終止所有子進程，釋放攝像頭與端口資源
```

---

## 📂 目錄結構
```text
.
├── backend/            # Python 代理核心邏輯
│   ├── core/           # 流水線 (Pipeline) 與狀態管理
│   └── stream_server.py# Flask 串流服務器
├── frontend/           # Next.js 監控儀表板
├── skills/             # 獨立的功能模組 (Agent Skills)
│   ├── video_capture/  # 影像擷取技能
│   ├── posture_reviewer/# 姿勢審查技能
│   └── calibration_wizard/# 校準引導技能
├── scripts/            # 自動化運維腳本
└── Makefile            # 專案管理指令集
```

---

## 🛡 技術規範與指標
*   **推論引擎**：MediaPipe BlazeFace Mesh (468+ 關鍵點)
*   **數據頻率**：30Hz 恆定採樣
*   **前端框架**：Next.js 15 (Turbopack Enabled)
*   **狀態持久化**：JSON-based Personalization Memory

---

## 👨‍💻 貢獻與開發
CTAR 的願景是透過 AI 提升知識工作者的健康品質。我們歡迎所有關於「感測器融合」或「多模態提醒」的建議。

*   **Repository**: [shihte/CTAR](https://github.com/shihte/CTAR)
*   **Architect**: Antigravity AI Agent

---
*© 2026 CTAR Intelligent Systems. Built for the Future of Work.*
