# 📦 外掛打包與安裝 (Plugin Manager)

RenUniversal 支援一鍵打包與安裝第三方開發者製作的**動作技能（Skills）**、**複合事件（Events）** 與**網頁體感遊戲（Apps）**。本文件說明外掛格式與打包／安裝流程。

> 回到 [文件中心](README.md)

---

## 1. 外掛宣告檔 (`.renuniversal`)

每個外掛是一個資料夾，內含一份 `.renuniversal` JSON 宣告檔，列出該外掛包含的模組與其相對路徑：

```json
{
  "name": "AppleCatchGame",
  "version": "1.0",
  "skills": ["skills/lean", "skills/squat"],
  "events": ["events/jump_event"],
  "apps": ["apps/apple_catch.html"]
}
```

| 欄位 | 說明 |
| :--- | :--- |
| `name` | 外掛名稱 |
| `version` | 版本字串 |
| `skills` | 動作判斷包目錄清單 |
| `events` | 複合事件規則目錄清單 |
| `apps` | 網頁應用 HTML 檔清單 |

---

## 2. 安裝外掛 (Install)

下載外掛資料夾後，透過套件管理指令安裝；系統會自動解析宣告檔，並將各模組安裝至對應的核心引擎目錄。

| 平台 | 指令 |
| :--- | :--- |
| **macOS / Linux** | `make install PATH=../下載的外掛資料夾` |
| **Windows** | `.\renuniversal.bat install ..\下載的外掛資料夾` |

安裝完成後，技能與事件會被 `ActionEngine` / `EventEngine` 熱載入，網頁應用會出現在 `http://<host>:8080/apps`。

---

## 3. 打包外掛 (Build)

官方打包工具會依你指定的模組路徑，自動提取檔案並生成 `.renuniversal` 宣告檔，輸出至 `dist/<NAME>/`。

### macOS / Linux
```bash
make build NAME=MyPlugin \
           SKILLS="skills/lean skills/turn" \
           EVENTS="events/bad_posture" \
           APPS="web/apps/mygame.html"
```

### Windows
```cmd
.\renuniversal.bat build --name MyPlugin ^
                         --skills skills/lean skills/turn ^
                         --events events/bad_posture ^
                         --apps web/apps/mygame.html
```

完成後 `dist/MyPlugin/` 即為完整安裝包，可直接上傳至 GitHub 分享。

---

## 4. 相關文件

- 撰寫技能的 `config.json` 與 `logic.py`：[動作判斷包開發](skills-development.md)
- 規則語法細節：[規則語法參考](rule-engine.md)
