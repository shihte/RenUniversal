# 🧩 動作判斷包開發 (Skills Development)

「動作判斷包（Skill）」是 RenUniversal 最小的姿態判定單元。系統的 `ActionEngine` 於運行時動態掃描 `skills/` 目錄，自動載入並執行每個判斷包。本文件說明如何開發自己的技能。

> 回到 [文件中心](README.md) ｜ 先看 [規則語法參考](rule-engine.md) 會更好上手。

---

## 1. 目錄結構

每個技能是 `skills/` 下的一個獨立子目錄：

```text
skills/
└── <your_skill_name>/
    ├── config.json   # 必要：宣告規則、描述與預設參數
    └── logic.py      # 選用：自訂判定邏輯（含 ActionDetector 類別）
```

| 檔案 | 是否必要 | 說明 |
| :--- | :---: | :--- |
| `config.json` | ✅ | 技能宣告檔，定義名稱、規則與預設偏好 |
| `logic.py` | ⬜ | 進階自訂邏輯；**省略時**系統自動套用通用幾何偵測器 |

---

## 2. 兩種開發路徑

RenUniversal 提供兩條路徑，視你的需求選擇：

| | 🟢 無程式碼（推薦） | 🔵 進階程式碼 |
| :--- | :--- | :--- |
| **需要 `logic.py`** | 否 | 是 |
| **判定核心** | `GenericActionDetector` | 你自訂的 `ActionDetector` |
| **點位寫法** | `f<n>` / `p<n>` 數字語法 | 數字語法或別名（`nose`, `chin`…） |
| **運算子** | `[x/y]?><` `[x/y]?<>` `[x/y]?>><<` `~~` + AND/OR/NOT | 自由，可用內建特徵鍵 |
| **適合場景** | 絕大多數兩點距離／越界判定 | 需要遲滯濾波、複合特徵或客製數學 |

---

## 3. 路徑 A：無程式碼（`config.json` + `rule_syntax`）

只需提供 `config.json` 並填寫 `rule_syntax`，系統即以 [`GenericActionDetector`](../backend/core/generic_skill_detector.py) 自動判定。**這是建議的預設做法。**

```json
{
  "name": "slouch",
  "description": "鼻子、下巴檢測縮短（低頭）",
  "enabled": true,
  "requirements": { "face_mesh": true, "pose": false },
  "rule_syntax": "f1,f152 >< num=20%",
  "default_preferences": { "slouch_threshold": 0.2 }
}
```

| 欄位 | 說明 |
| :--- | :--- |
| `name` | 技能識別名（亦作為 metric／事件引用名） |
| `description` | 人類可讀描述 |
| `enabled` | 是否啟用；`false` 則略過載入 |
| `requirements` | 感測需求，如 `{ "face_mesh": true, "pose": true }` |
| `rule_syntax` | 規則字串，語法見 [規則語法參考](rule-engine.md) |
| `default_preferences` | 預設門檻，會注入全域偏好供 slider 調整 |

> 此路徑的點位**僅支援** `f<n>` / `p<n>` 數字寫法（如 `f1`、`p11`），不支援文字別名。完整運算子與事件組合請見 [規則語法參考](rule-engine.md)。

---

## 4. 路徑 B：進階自訂 `logic.py`

當你需要遲滯濾波（hysteresis）、多特徵複合判定或自訂數學時，新增 `logic.py` 並實作 `ActionDetector` 類別。可直接參考或繼承 [`backend/core/skill_template.py`](../backend/core/skill_template.py)。

```python
from typing import Tuple, Dict, Any

class ActionDetector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def evaluate(self,
                 face_landmarks: Any,
                 pose_landmarks: Any,
                 face_dim: Tuple[int, int],
                 body_dim: Tuple[int, int],
                 baselines: Dict[str, float],
                 preferences: Dict[str, Any],
                 state_history: Dict[str, Any]) -> Tuple[bool, float, Dict[str, Any]]:
        """
        評估當前訊號是否觸發此技能。

        參數:
          - face_landmarks / pose_landmarks : MediaPipe 臉部與身體地標
          - face_dim / body_dim            : (width, height) 解析度
          - baselines                       : 校準基準值（eye_distance、nose_chin_distance、
                                              shoulder_width、shoulder_midpoint_x/y…）
          - preferences                     : 全域使用者偏好（含各門檻）
          - state_history                   : 上一輪狀態（如 is_bad_posture，可用於遲滯）

        回傳:
          - is_bad      (bool)  : 是否判定觸發
          - primary_val (float) : 主要特徵值（供前端圖表）
          - info        (dict)  : 額外診斷資訊（回傳前端顯示）
        """
        ...
```

### 內建特徵鍵 (Built-in Feature Keys)
若以 `skill_template.py` 為基礎，可直接取用其預先計算的特徵，並用結構化規則（dict 格式）比較：

| 特徵鍵 | 意義 |
| :--- | :--- |
| `nose_chin_ratio` | 低頭比例（正常 0.0，前傾時為負值，內建轉頭容差與遲滯） |
| `torso_sway` | 軀幹水平搖晃比 |
| `torso_lean` | 軀幹前傾比 |
| `shoulder_slope` | 肩部傾斜斜率 |
| `yaw_deviation` | 頭部左右偏轉比 |

結構化規則範例（運算子支援 `>` `<` `>=` `<=` `==`）：
```json
{
  "name": "lean",
  "description": "軀幹前傾判定模組",
  "enabled": true,
  "requirements": { "pose": true },
  "rules": [
    { "feature": "torso_lean", "operator": ">", "threshold_key": "lean_threshold" }
  ],
  "default_preferences": { "lean_threshold": 0.12 }
}
```

> `skill_template` 的字串規則路徑另支援文字別名（`nose`, `chin`, `left_eye`, `right_eye`, `left_shoulder`, `right_shoulder`），這是 Generic 路徑所沒有的。

---

## 5. 熱載入與註冊流程

1. **掃描**：啟動或呼叫 reload 時，[`action_engine.py`](../backend/core/action_engine.py) 掃描 `skills/*/config.json`。
2. **派發**：有 `logic.py` → 載入其 `ActionDetector`；無 → 套用 `GenericActionDetector`。
3. **注入偏好**：`default_preferences` 併入全域設定，供 Web slider 即時調參。
4. **前端控制**：`/api/skills` 系列端點可動態建立、開關、修改與刪除技能，變更後自動 reload。

---

## 6. 延伸閱讀

- [規則語法參考](rule-engine.md) — 點位、運算子、事件組合的完整定義
- [外掛打包與安裝](plugins.md) — 將你的技能打包成可分享的外掛
- [系統架構與演算法](DETAILED_ARCHITECTURE.md) — 幾何特徵的數學原理
