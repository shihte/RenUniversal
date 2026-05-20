# CTAR 動作判斷包設計規範與開發指引 (Action Judgment Packages)

本目錄存放所有自定義的動作與姿態偵測模組。系統底層偵測核心（Pipeline）採用動態反射與插件註冊模式，於運行時自動掃描、加載並執行此目錄下的判斷包。

---

## 1. 動作判定包目錄結構
每一個自定義的動作判斷模組必須為一個獨立的子目錄，且應包含以下核心檔案：

```text
skills/
└── [your_skill_name]/
    ├── config.json  # 宣告特徵匹配規則、操作運算元與預設閥值
    └── logic.py     # 判定邏輯的進入點 (繼承或引用通用解析範本)
```

---

## 2. 規則配置規範 (`config.json` Schema)

`config.json` 是動作判斷包的聲明文件，定義了該技能所需訂閱的感測資料類型、判定門檻及運算規則。

### 欄位說明與範例：

```json
{
  "name": "slouch",
  "description": "駝背/前傾坐姿判定模組",
  "enabled": true,
  "requirements": {
    "face_mesh": true,
    "pose": true
  },
  "rules": [
    {
      "feature": "nose_chin_ratio",
      "operator": "<",
      "threshold_key": "slouch_threshold"
    },
    {
      "feature": "torso_lean",
      "operator": ">",
      "threshold_key": "lean_threshold"
    }
  ],
  "default_preferences": {
    "slouch_threshold": -0.15,
    "lean_threshold": 0.12
  }
}
```

### 支援判定特徵 (Supported Feature Keys)
*   `nose_chin_ratio`：低頭比例（基於面部網格垂直距離變化，正常值為 0.0，低頭前傾時為負值）。
*   `torso_sway`：軀幹水平搖晃比（肩膀中心點水平偏移相對於影像寬度比例）。
*   `torso_lean`：軀幹前傾比（雙肩至雙髖垂直距離縮短比例）。
*   `shoulder_slope`：肩部傾斜斜率（左右肩膀傾斜角度）。
*   `yaw_deviation`：頭部左右偏轉比（左右眼距比例偏差值）。

### 運算元 (Operators)
支援：`>` (大於), `<` (小於), `>=` (大於等於), `<=` (小於等於), `==` (等於)。

---

## 3. 邏輯驅動規範 (`logic.py`)
`logic.py` 是引擎加載的邏輯入口，預設模版將自動匹配 `config.json` 中配置的規則鏈。所有自定義判斷包皆可複用系統的核心判定驅動：

```python
from backend.core.skill_template import BaseActionSkill

class ActionSkill(BaseActionSkill):
    """
    通用動作判定器。
    基於 config.json 中定義的 rules 列表動態求值，判定當前姿態是否成立。
    """
    pass
```

---

## 4. 動態熱載入與註冊流程
1. **目錄掃描**：`backend/core/action_engine.py` 於啟動時尋找 `skills/*/config.json`。
2. **規則解析**：引擎解析 `config.json` 後將規則注入判定流水線，同時將其 `default_preferences` 合併至全局狀態機中的 `preferences.json`。
3. **前端橋接**：`/api/skills` 接口將動態返回當前所有加載的動作判定包及其開關、門檻配置，以降低非技術使用者的調整門檻。
