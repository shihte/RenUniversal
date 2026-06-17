# 🚀 安裝與快速啟動指南 (Getting Started)

本指南說明如何在桌面端（Python 伺服器）安裝並啟動 RenUniversal。若你只想在 iPhone/iPad 上使用，請改看 [iOS 原生 App](iOS_Native_App.md)。

> 回到 [文件中心](README.md)

---

## 1. 系統需求 (Prerequisites)

| 項目 | 需求 |
| :--- | :--- |
| **作業系統** | macOS 12.0+、Linux (Ubuntu 20.04+)、Windows 10/11 |
| **Python** | 3.8 – 3.11 |
| **硬體** | 具備 UVC 協定的 USB／內建相機，或可連線的行動裝置瀏覽器 |

> 💡 **Windows 相容性提示**：相機調用邏輯升級後理論上已全面跨平台，但 Windows 本機鏡頭尚未經大規模測試。若遇鏡頭異常，建議改用手機掃描 QR Code 作為副鏡頭。

---

## 2. 取得專案

```bash
git clone https://github.com/shihte/RenUniversal.git
cd RenUniversal
```

---

## 3. 安裝與啟動

### macOS / Linux（Makefile）

| 指令 | 用途 |
| :--- | :--- |
| `make setup` | 初始化虛擬環境、安裝依賴並下載 MediaPipe 模型 |
| `make run` | 前景啟動伺服器 |
| `make start` | 背景守護進程啟動（日誌轉拋至 `agent.log`） |
| `make stop` | 停止背景伺服器 |
| `make restart` | 重新啟動背景伺服器 |
| `make status` | 查看背景伺服器狀態 |
| `make cli` | 純命令列（headless）模式，事件以 JSON 輸出至 stdout |
| `make clean` | 清除快取與日誌 |
| `make doctor` | 環境診斷 |
| `make install PATH=<外掛路徑>` | 安裝第三方外掛（見 [外掛文件](plugins.md)） |
| `make build NAME=... SKILLS=... EVENTS=... APPS=...` | 打包外掛（見 [外掛文件](plugins.md)） |

啟動後預設於 **http://127.0.0.1:8080** 提供 Web 監控儀表板。

### Windows（批次檔）

> **注意**：在 PowerShell 中需加 `.\` 前綴；CMD 中可省略。

| 指令 | 用途 |
| :--- | :--- |
| `.\renuniversal.bat doctor` | 環境診斷 |
| `.\renuniversal.bat setup` | 初始化虛擬環境、依賴安裝與 AI 模型下載 |
| `.\renuniversal.bat run` | 前景啟動系統伺服器（Ctrl+C 停止） |
| `.\renuniversal.bat start` | 背景啟動系統伺服器 |
| `.\renuniversal.bat stop` | 停止背景伺服器 |
| `.\renuniversal.bat restart` | 重啟背景伺服器 |
| `.\renuniversal.bat status` | 顯示伺服器狀態 |
| `.\renuniversal.bat cli` | 純命令列（headless）模式，事件以 JSON 輸出至 stdout |
| `.\renuniversal.bat clean` | 清除快取與日誌 |
| `.\renuniversal.bat install <路徑>` | 安裝外掛套件 |
| `.\renuniversal.bat build --name ... --skills ... --events ... --apps ...` | 打包外掛 |

---

## 4. 進階啟動參數 (CLI Flags)

`make run` / `make start` 可透過 `ARGS="..."` 傳入參數；Windows 直接附加於指令後。

```bash
# macOS / Linux 範例
make start ARGS="--host 0.0.0.0 --enable-tunnel --auth admin:1234"

# Windows 範例（PowerShell）
.\renuniversal.bat run --host 0.0.0.0 --enable-tunnel --auth admin:1234
```

| 參數 | 說明 |
| :--- | :--- |
| `--host 0.0.0.0` | 綁定所有網路介面，開放區網內手機／其他裝置連線（預設 `127.0.0.1`，僅本機） |
| `--port <N>` | 指定 HTTP 連接埠（預設 `8080`；另有 HTTPS `8443` 供手機 Secure Context） |
| `--enable-tunnel` | 啟動 localhost.run 外網穿透，將服務曝露至公網 |
| `--auth user:pass` | 設定 Basic Auth 連線帳密 |
| `--disable-privacy` | 預設關閉臉部隱私打碼模式 |
| `--cli` | 純 headless 模式，不啟動 Web 伺服器 |

> 🔐 **安全提醒**：當以 `--host 0.0.0.0` 或 `--enable-tunnel` 對外開放、但未提供 `--auth` 時，系統會**自動產生隨機帳密並顯示於終端機**，避免服務裸奔。對外部署的完整建議請見 [隱私保護與資安](privacy-and-security.md)。

---

## 5. 連線方式

| 入口 | 網址 | 用途 |
| :--- | :--- | :--- |
| 監控儀表板 | `http://<host>:8080/` | 主控台、即時影像與狀態 |
| 相機設定頁 | `http://<host>:8080/camera` | 技能／事件管理與校準 |
| 手機副鏡頭 | `https://<local_ip>:8443/mobile` | 手機瀏覽器推送畫面（需 HTTPS Secure Context） |
| 應用啟動器 | `http://<host>:8080/apps` | 已安裝的網頁體感應用 |

> 📷 手機作為副鏡頭時，因瀏覽器要求安全內容，請使用 **HTTPS（埠 8443）**；首次連線需信任自簽憑證。

---

## 6. 下一步

- 想自訂姿態判定？閱讀 [規則語法參考](rule-engine.md)。
- 想開發完整技能？閱讀 [動作判斷包開發](skills-development.md)。
- 想理解底層原理？閱讀 [系統架構與演算法](DETAILED_ARCHITECTURE.md)。
