# 🚀 RenUniversal：智慧生理姿態與復健監控開放平台

[![Python](https://img.shields.io/badge/Python-3.8--3.11-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-teal.svg?style=for-the-badge&logo=google)](https://mediapipe.dev/)
[![iOS](https://img.shields.io/badge/iOS-15.0+-black.svg?style=for-the-badge&logo=apple)](docs/iOS_Native_App.md)
[![Architecture](https://img.shields.io/badge/Architecture-Agentic--Modular-orange.svg?style=for-the-badge)](docs/DETAILED_ARCHITECTURE.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

> 基於電腦視覺邊緣運算（Edge Computing）的 **AI 生理姿態回饋與即時監控系統**。

RenUniversal 起初專為輔助 **CTAR（Chin-tuck Against Resistance，下巴內縮抗阻力運動）** 吞嚥復健訓練提供即時姿態評估，現已升級為高度開放的 **多代理人技能架構（Agent Skills Architecture）** 體感互動平台。系統摒棄硬編碼判定邏輯，臨床人員與開發者可自由抽換、擴充姿態判定規則與體感應用。

---

## ✨ 核心亮點

| 特色 | 說明 |
| :--- | :--- |
| 📱 **原生 iOS App** | 100% 終端邊緣運算、榨乾 Apple Neural Engine，零網路延遲 60 FPS |
| 🎥 **動態多鏡頭融合** | 自動掃描所有連線鏡頭，無縫融合臉部（FaceMesh）與身體（Pose）特徵 |
| 🧩 **熱插拔技能引擎** | 運行時動態載入 `skills/` 判定包，免重編譯核心 |
| 🔗 **高階事件組合** | 將底層動作特徵以邏輯運算（AND/OR/NOT）組合成複合事件 |
| 🛡 **硬體級臉部打碼** | 即時高斯模糊保護隱私，且不影響姿態判定 |
| 📦 **第三方外掛框架** | 一鍵打包與安裝 Skills / Events / 網頁遊戲 |

---

## ⚡ 快速開始

```bash
git clone https://github.com/shihte/RenUniversal.git
cd RenUniversal
```

**Mac / Linux**
```bash
make setup      # 安裝依賴與模型
make run        # 前景啟動（http://127.0.0.1:8080）
```

**Windows**
```cmd
renuniversal.bat setup
renuniversal.bat run
```

完整的安裝需求、進階啟動參數與外網穿透設定，請見 **[安裝與快速啟動指南](docs/getting-started.md)**。

---

## 📚 文件中心

所有詳細文件已分類整理至 **[`docs/`](docs/README.md)**：

| 文件 | 內容 |
| :--- | :--- |
| 📖 [文件總覽](docs/README.md) | 文件導覽索引 |
| 🚀 [安裝與快速啟動](docs/getting-started.md) | 環境需求、安裝、啟動參數、區網／外網部署 |
| 🏛 [系統架構與演算法](docs/DETAILED_ARCHITECTURE.md) | 系統拓撲、幾何演算法、設計模式 |
| 📐 [規則語法參考](docs/rule-engine.md) | 點位語法、幾何運算子、事件組合 |
| 🧩 [動作判斷包開發](docs/skills-development.md) | 撰寫自訂 Skill 與 `config.json` 規範 |
| 📦 [外掛打包與安裝](docs/plugins.md) | Plugin Manager 與 `.renuniversal` 宣告檔 |
| 🛡 [隱私保護與資安](docs/privacy-and-security.md) | 臉部打碼機制與後端資安強化 |
| 📱 [iOS 原生 App](docs/iOS_Native_App.md) | iOS 版介紹、下載與編譯部署 |

---

## 📜 授權

本專案採用 MIT License，詳見 [LICENSE](LICENSE)。

Copyright (c) 2026 RenUniversal Project Contributors.
