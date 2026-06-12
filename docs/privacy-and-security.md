# 🛡 隱私保護與資安 (Privacy & Security)

RenUniversal 處理即時人臉影像，隱私與安全是設計核心。本文件說明前端的臉部打碼機制、後端的資安強化措施，以及對外部署時的建議。

> 回到 [文件中心](README.md)

---

## 1. 臉部隱私打碼 (Face Privacy Blur)

系統內建硬體層級的即時臉部馬賽克，於影像處理底層運作：

- **多鏡頭零死角防護**：無論主機鏡頭或任意數量的 Wi-Fi 手機副鏡頭，只要畫面偵測到臉部即立刻高斯模糊。
- **超大廣角包覆**：依臉部追蹤點邊界向外擴張 **150%** 防護區，連同頭髮邊緣、耳朵與脖子一併遮蔽。
- **不影響姿態判定**：姿態追蹤點（鼻尖、下巴、雙肩等）疊加於模糊層之上，即使臉部完全馬賽克，仍能精準判定低頭或代償動作。
- **即時動態開關**：可透過 Web 介面一鍵開關隱私模式，狀態即時同步至 `preferences.json` 並於下次啟動沿用。

> 預設**啟用**隱私模式；以 `--disable-privacy` 啟動可預設關閉。實作位於 [`pipeline.py`](../backend/core/pipeline.py) 的 privacy blur 區段。

---

## 2. 後端資安強化 (Backend Hardening)

以下為已落實的安全措施，對應原始碼如註明。

### 2.1 規則引擎防注入：AST 白名單求值器
姿態與事件規則來自使用者輸入（API 寫入的 `rule_syntax`）。系統**不使用** `eval()` 直接執行，而是經 [`safe_eval.py`](../backend/core/safe_eval.py) 的 AST 白名單求值：

- 規則先被解析、子條件替換為 `True`/`False`；
- 最終運算式以 `ast.parse` 解析，**僅允許** `BoolOp`／`UnaryOp`／`And`／`Or`／`Not`／布林常數／括號；
- 任何函式呼叫、屬性存取、算術運算、名稱參照都會被拒絕並安全失敗（判定為不觸發）。

→ 徹底杜絕透過規則字串進行的任意程式碼執行（RCE）。

### 2.2 網路來源防護：自動驅逐與數量上限
`/upload_frame` 接受手機副鏡頭推送的影格，以 `source` 參數區分來源。為避免惡意端以大量不同 `source_id` 撐爆記憶體（DoS），[`state.py`](../backend/core/state.py) 的 `update_network_frame`：

- 每次寫入時**驅逐超過 TTL（10 秒）的過期來源**；
- 限制同時最多 **16 個來源**，超過時淘汰最舊的一筆。

### 2.3 請求體強健性：統一 JSON 防護
所有寫入型 API（`/settings`、`/control`、skills／events 的 create／toggle／delete、`/api/settings/update`）改用統一的 `get_json_or_400()` 解析：空 body 或非合法 JSON 會回傳乾淨的 **HTTP 400**，而非未處理例外造成的 500。

### 2.4 連線存取控制 (Basic Auth)
當以 `--host 0.0.0.0` 或 `--enable-tunnel` 對外開放、卻未提供 `--auth` 時，系統會以 `secrets` 模組**自動產生 12 字元隨機帳密**並顯示於終端機，避免服務無認證裸奔。亦可用 `--auth user:pass` 自訂。

---

## 3. 對外部署建議 (Deployment Checklist)

當你打算讓本機以外的裝置連線時，建議：

- [ ] **務必設定 `--auth`**：使用高強度自訂帳密，勿長期沿用自動產生值。
- [ ] **優先走 HTTPS（埠 8443）**：手機副鏡頭因 Secure Context 需求本就走 HTTPS；首次連線需信任自簽憑證。
- [ ] **`--enable-tunnel` 謹慎使用**：localhost.run 會將服務曝露至**公網**，僅在必要時開啟，用畢即關閉。
- [ ] **信任的外掛來源**：安裝外掛等同在本機執行其 `logic.py`（動態載入）。僅安裝來源可信的外掛，詳見 [外掛文件](plugins.md)。
- [ ] **保護 `preferences.json`**：內含個人化基準與偏好，已列入 `.gitignore`，勿提交至版本庫。

> ⚠️ 自簽（adhoc）憑證適用於開發與區網，無法防範進階中間人攻擊；正式對外服務應改用受信任憑證並置於反向代理之後。

---

## 4. 相關原始碼

| 檔案 | 職責 |
| :--- | :--- |
| [`backend/core/safe_eval.py`](../backend/core/safe_eval.py) | AST 白名單布林求值器 |
| [`backend/core/state.py`](../backend/core/state.py) | 共享狀態、網路來源驅逐與持久化 |
| [`backend/core/pipeline.py`](../backend/core/pipeline.py) | 影像流水線與臉部隱私打碼 |
| [`backend/stream_server.py`](../backend/stream_server.py) | Flask 路由、Basic Auth、JSON 請求防護 |
