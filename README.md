# 🚀 RenUniversal：智慧生理姿態與復健監控開放平台

[![Python](https://img.shields.io/badge/Python-3.8--3.11-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-teal.svg?style=for-the-badge&logo=google)](https://mediapipe.dev/)
[![iOS](https://img.shields.io/badge/iOS-15.0+-black.svg?style=for-the-badge&logo=apple)](docs/iOS_Native_App.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

> 基於電腦視覺邊緣運算的 **AI 生理姿態回饋與即時監控系統**。起初輔助 **CTAR 吞嚥復健**，現為高度開放的多代理人技能平台——臨床人員與開發者可自由抽換、擴充姿態判定規則與體感應用。

---

## ⚡ 快速開始

```bash
git clone https://github.com/shihte/RenUniversal.git && cd RenUniversal
make setup && make run      # Windows: renuniversal.bat setup && renuniversal.bat run
```

啟動後開啟 **http://127.0.0.1:8080**。完整需求、啟動參數與部署方式請見 **[安裝與快速啟動指南 →](docs/getting-started.md)**

---

## 📚 文件導航

> 不確定從哪開始？先到 **[文件中心 →](docs/README.md)** 依角色（使用者／開發者）導覽。

| 我想… | 文件 |
| :--- | :--- |
| 🚀 把系統安裝並跑起來 | [安裝與快速啟動](docs/getting-started.md) |
| 📱 用 iPhone／iPad（最佳體驗，免架站） | [iOS 原生 App](docs/iOS_Native_App.md) |
| 📐 自訂姿態判定規則 | [規則語法參考](docs/rule-engine.md) |
| 🧩 開發自己的動作判斷技能 | [動作判斷包開發](docs/skills-development.md) |
| 📦 打包／安裝第三方外掛 | [外掛打包與安裝](docs/plugins.md) |
| 🏛 理解系統架構與演算法 | [系統架構與演算法](docs/DETAILED_ARCHITECTURE.md) |
| 🔬 深入核心實作與生命週期 | [進階技術細節 (Internals)](docs/internals/README.md) |
| 🛡 了解隱私保護與資安 | [隱私保護與資安](docs/privacy-and-security.md) |

---

<sub>MIT License — 詳見 [LICENSE](LICENSE)　·　Copyright (c) 2026 RenUniversal Project Contributors.</sub>
