# 🚀 RenUniversal：智慧生理姿態與復健監控開放平台

[![Python](https://img.shields.io/badge/Python-3.8--3.11-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-teal.svg?style=for-the-badge&logo=google)](https://mediapipe.dev/)
[![Architecture](https://img.shields.io/badge/Architecture-Agentic--Modular-orange.svg?style=for-the-badge)](https://github.com/shihte/RenUniversal)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**CTAR（Chin-tuck Against Resistance，下巴內縮抗阻力運動）** 是一種專業的吞嚥復健訓練。透過對抗阻力，能有效強化舌骨上肌群，改善喉部上提不足及上食道括約肌運動，幫助吞嚥障礙患者恢復由口進食。

本專案是一個基於電腦視覺邊緣運算（Edge Computing）的 **AI 生理姿態回饋與即時監控系統**。起初專為輔助患者在進行 CTAR 訓練時提供正確的姿態即時評估，現已全面升級為 **「RenUniversal 高度開放式體感互動平台」**。

系統摒棄了傳統的硬編碼與線性判定邏輯，導入了高度模組化與高通用性的 **多代理人技能架構（Agent Skills Architecture）** 與 **第三方外掛安裝機制**，使臨床人員或開發者能輕易抽換、擴充不同的姿態判定邏輯與體感應用遊戲。

---

## 🔬 核心技術與模組化通用架構 (Modularity & Generalizability)

### 1. 智慧動態多鏡頭掃描 (Dynamic Multi-Camera Inference)
系統支援**多相機陣列並行運算**。無論你是用電腦鏡頭拍臉、手機拍身體，或是隨意擺放，底層 AI 流水線會**強制掃描所有連線中的鏡頭畫面**，自動標定含有完整臉部 (FaceMesh) 或身體骨架 (Pose) 的鏡頭源並進行特徵無縫融合，完全免除手動指定鏡頭順序的麻煩，實現零死角追蹤。

### 2. 動態插件規則引擎 (Action & Event Engine)
本系統的極致通用性建立在其**「技能模組化 (Skills Modularity)」**與**「事件分離 (Event Pipeline)」**設計上：
*   **熱插拔技能 (Hot-Pluggable Agent Skills)**：`ActionEngine` 於運行時會動態反射式掃描 `skills/` 目錄下的判定包。開發者只需依照 JSON 配置規則新增目錄，無需重寫編譯核心框架，即可為系統擴充全新的身體動作特徵判定。
*   **高階事件組合 (Event Engine)**：底層偵測到的單一動作特徵，會被傳遞給 Event Engine 進行高階邏輯判定。這種底層「特徵」與高層「事件」解耦的設計，讓系統不再侷限於單一復健動作。

### 3. 三維姿態幾何評估演算法 (Feature Vector Mathematics)
系統利用 MediaPipe Landmark 提取特徵座標進行三維向量投影，量化人體生理姿態（例如計算鼻尖與下巴的垂直比例變化來判定低頭角度，或是肩峰點連線斜率以偵測軀幹代償偏移）。同時內建**磁滯抗噪濾波器 (Hysteresis Filter)**，防止臨界狀態震盪，大幅降低高頻環境抖動引起的誤報。

---

## 📦 第三方外掛安裝框架 (Plugin Manager)

RenUniversal 現在支援一鍵安裝第三方開發者製作的動作、事件與網頁遊戲。
開發者只需要將功能打包成資料夾，並在內附帶一個 `.renuniversal` 宣告檔：

```json
{
  "name": "AppleCatchGame",
  "version": "1.0",
  "skills": ["skills/lean", "skills/squat"],
  "events": ["events/jump_event"],
  "apps": ["apps/apple_catch.html"]
}
```

下載後，只需透過指令安裝：
* **Mac/Linux:** `make install PATH=../下載的外掛資料夾`
* **Windows:** `renuniversal.bat install ..\下載的外掛資料夾`

系統會自動解析並將所有模組安裝至正確的核心引擎目錄中。

### 🛠 如何打包自己的外掛 (Plugin Builder)
我們提供了官方的打包工具，讓你一鍵將寫好的 Skills / Events / Apps 提取並自動生成 `.renuniversal`：

**Mac / Linux:**
```bash
make build NAME=MyPlugin SKILLS="skills/lean skills/turn" EVENTS="events/bad_posture" APPS="web/apps/mygame.html"
```

**Windows:**
```cmd
renuniversal.bat build --name MyPlugin --skills skills/lean skills/turn --events events/bad_posture --apps web/apps/mygame.html
```
執行後，系統會在 `dist/MyPlugin/` 產出完美的安裝包，你可以直接上傳到 GitHub 分享！

---

## 🛠 開發先前條件 (Prerequisites)

*   **作業系統**：macOS (12.0+), Linux (Ubuntu 20.04+), Windows 10/11
*   **Python 版本**：**Python 3.8 至 Python 3.11** (因 MediaPipe 原生編譯二進制檔限制，不支援更高或更低版本)
*   **硬體要求**：具備 UVC 協定的 USB 外接相機 或 行動裝置瀏覽器連線。

---

## 🚀 快速部署引導 (Cloning & Setup)

### 1. 複製專案庫
```bash
git clone https://github.com/shihte/RenUniversal.git
cd RenUniversal
```

### 2. 環境初始化與運行 (Windows)
Windows 使用者請直接透過專屬的批次檔管理專案：
1. **初始化與依賴安裝**：`renuniversal.bat setup` (具備動態進度顯示，無冗長日誌)
2. **啟動系統伺服器**：`renuniversal.bat run`
3. **執行架構驗證測試**：`renuniversal.bat test`
4. **清除快取與日誌**：`renuniversal.bat clean`
5. **安裝外掛套件**：`renuniversal.bat install <路徑>`

### 3. 環境初始化與運行 (Mac / Linux)
使用 Makefile 工具包：
1. **初始化與依賴安裝**：`make setup`
2. **前景啟動系統**：`make run`
3. **背景守護進程啟動**：`make start` (執行日誌會轉拋至 agent.log)
4. **停止背景伺服器**：`make stop`
5. **執行架構驗證測試**：`make test`
6. **安裝外掛套件**：`make install PATH=<路徑>`

> **關於 `make test` / `renuniversal.bat test` 是做什麼的？**
> 這會觸發 `backend/test_architecture.py` 測試腳本，目的是用來驗證系統核心層的 `SharedState` (執行緒安全共享狀態管理器) 以及 Pydantic 的資料型別 Schema (如 `DetectorStatus`) 能否在極端的併發模擬下正確初始化、安全鎖定並無損序列化。這是一項確保記憶體存取安全的微型單元測試。

---

## 📜 授權聲明 (License)

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 RenUniversal Project Contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
