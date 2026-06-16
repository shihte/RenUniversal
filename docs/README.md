# 📚 RenUniversal 文件中心 (Documentation Hub)

歡迎來到 RenUniversal 的文件總覽。所有文件依用途分類如下，請依需求選讀。

> 回到 [專案首頁 README](../README.md)

---

## 🧭 依角色導覽

### 我是使用者 / 臨床人員
想直接把系統跑起來、用手機或電腦做姿態監控。
1. [安裝與快速啟動](getting-started.md) — 環境需求、安裝、啟動
2. [iOS 原生 App](iOS_Native_App.md) — 免架站、一鍵安裝的最佳體驗
3. [隱私保護與資安](privacy-and-security.md) — 了解臉部打碼與連線安全

### 我是開發者 / 想擴充功能
想自訂姿態判定規則、開發技能或打包外掛。
1. [系統架構與演算法](DETAILED_ARCHITECTURE.md) — 先理解整體設計
2. [規則語法參考](rule-engine.md) — 點位、運算子與事件組合
3. [動作判斷包開發](skills-development.md) — 撰寫自訂 Skill
4. [外掛打包與安裝](plugins.md) — 分享你的成果
5. [進階技術細節 (Internals)](internals/README.md) — 要改核心？深入實作與生命週期

---

## 📂 文件分類總表

### 入門 (Getting Started)
| 文件 | 說明 |
| :--- | :--- |
| [getting-started.md](getting-started.md) | 系統需求、依賴安裝、前景／背景啟動、CLI 參數、區網與外網穿透部署 |

### 架構與原理 (Architecture)
| 文件 | 說明 |
| :--- | :--- |
| [DETAILED_ARCHITECTURE.md](DETAILED_ARCHITECTURE.md) | 系統拓撲、資料流、幾何特徵演算法、核心設計模式對照 |
| [rule-engine.md](rule-engine.md) | 規則引擎語法完整參考：點位 ID、四種幾何運算子、事件邏輯組合 |

### 深入實作 (Internals)
| 文件 | 說明 |
| :--- | :--- |
| [internals/](internals/README.md) | 進階技術細節索引：含全景資料流圖 |
| [internals/pipeline.md](internals/pipeline.md) | `run_cycle()` 生命週期流程圖、多鏡頭融合、效能特性 |
| [internals/state-and-concurrency.md](internals/state-and-concurrency.md) | 執行緒拓撲、三把鎖、來源驅逐、偏好持久化 |
| [internals/rule-evaluation.md](internals/rule-evaluation.md) | 規則轉換管線、幾何模式判定、AST 安全求值 |
| [internals/http-api.md](internals/http-api.md) | 請求生命週期、完整端點清單、輸入防護 |

### 開發與擴充 (Development)
| 文件 | 說明 |
| :--- | :--- |
| [skills-development.md](skills-development.md) | 動作判斷包目錄結構、`config.json` 規範、`logic.py` 進階實作 |
| [plugins.md](plugins.md) | 第三方外掛打包（`make build`）與安裝（`make install`）流程 |

### 安全與部署 (Operations)
| 文件 | 說明 |
| :--- | :--- |
| [privacy-and-security.md](privacy-and-security.md) | 臉部隱私打碼機制、後端資安強化措施與對外部署建議 |

### 平台 (Platforms)
| 文件 | 說明 |
| :--- | :--- |
| [iOS_Native_App.md](iOS_Native_App.md) | iOS 原生版介紹、IPA 下載、側載與 Xcode 編譯部署 |

---

## 📝 文件慣例

- 所有路徑均以**專案根目錄**為基準（例如 `skills/slouch/config.json`）。
- 程式碼區塊標註語言以利語法高亮；數學式採用 LaTeX（`$$...$$`）。
- 架構圖以 [Mermaid](https://mermaid.js.org/) 撰寫，於 GitHub 上可直接渲染。
