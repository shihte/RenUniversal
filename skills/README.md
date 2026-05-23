# RenUniversal 動作判斷包設計規範與開發指引 (Action Judgment Packages)

本目錄存放所有自定義的動作與姿態偵測模組。系統底層偵測核心（Pipeline）採用動態插件模式，於運行時自動掃描、加載並執行此目錄下的判斷包。

---

## 1. 動作判定包目錄結構
每一個自定義的動作判斷模組必須為一個獨立的子目錄，且應包含以下核心檔案：

```text
skills/
└── [your_skill_name]/
    ├── config.json  # 宣告特徵匹配規則、描述與預設配置
    └── logic.py     # 判定邏輯的實作進入點 (包含 ActionDetector 類別)
```

---

## 2. 規則配置規範 (`config.json` Schema)

`config.json` 是動作判斷包的聲明文件，定義了該技能的名稱、啟動狀態、感測器需求、特徵運算規則以及預設參數。

系統支援兩種規則配置格式：**自定義幾何語法 (推薦)** 與 **傳統結構化規則**。

### A. 自定義幾何語法格式 (推薦)
此格式使用簡潔直觀的字串來定義點位之間的距離變化關係。語法格式如下：
```text
[點位1],[點位2] [方向算元] [百分比]
```

*   **方向算元說明**：
    *   `><`：縮短 (Shrink) -> 當前距離比基準值縮小達指定比例。
    *   `<>`：拉長 (Expand) -> 當前距離比基準值放大達指定比例。
    *   `>><<`：雙向偏差 (Both) -> 當前距離與基準值的偏差絕對值達指定比例。
*   **百分比表示法**：可為 `20%` 或 `num=20` (皆代表 20% 的變化閾值)。
*   **點位表示法**：支援英文別名或 Mediapipe Landmark 的整數索引。
    *   **支援的點位別名 (POINT_ALIASES)**：`nose`, `chin`, `left_eye`, `right_eye`, `left_shoulder`, `right_shoulder`
    *   **數字索引**：例如 `33` (左眼點位), `263` (右眼點位), `1` (鼻尖點位)。

#### 範例：
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
    "nose,chin >< 20%"
  ],
  "default_preferences": {
    "slouch_threshold": 0.20,
    "yaw_tolerance": 0.10
  }
}
```

### B. 傳統結構化規則格式
傳統格式適合訂閱內部已計算好的特徵比率：
```json
{
  "name": "lean",
  "description": "軀幹前傾判定模組",
  "enabled": true,
  "requirements": {
    "pose": true
  },
  "rules": [
    {
      "feature": "torso_lean",
      "operator": ">",
      "threshold_key": "lean_threshold"
    }
  ],
  "default_preferences": {
    "lean_threshold": 0.12
  }
}
```

#### 支援的內建特徵 (Built-in Feature Keys)：
*   `nose_chin_ratio`：低頭比例（正常值為 0.0，低頭前傾時為負值）。
*   `torso_sway`：軀幹水平搖晃比。
*   `torso_lean`：軀幹前傾比。
*   `shoulder_slope`：肩部傾斜斜率。
*   `yaw_deviation`：頭部左右偏轉比。

---

## 3. 邏輯實作規範 (`logic.py`)
`logic.py` 必須實作一個名為 `ActionDetector` 的類別，該類別需提供 `__init__` 與 `evaluate` 方法：

```python
from typing import Tuple, Dict, Any

class ActionDetector:
    def __init__(self, config: Dict[str, Any]):
        """
        初始化偵測器，傳入該技能的 config 字典
        """
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
        
        傳入參數:
          - face_landmarks: Mediapipe Face Mesh 訊號
          - pose_landmarks: Mediapipe Pose 訊號
          - face_dim: (width, height) 臉部區域解析度
          - body_dim: (width, height) 全身區域解析度
          - baselines: 基準值字典 (包含 "eye_distance", "nose_chin_distance", "shoulder_width" 等)
          - preferences: 全局使用者喜好設定 (內含各門檻值)
          - state_history: 歷史狀態字典 (包含 "is_bad_posture" 等，可用於遲滯過濾)
          
        回傳值:
          - is_bad (bool): 是否判定為不良姿勢
          - primary_val (float): 主要特徵值 (供圖表繪製使用)
          - info (dict): 額外的診斷資訊 (會傳送回前端顯示)
        """
        # 可以直接繼承或引用 backend/core/skill_template.py 中的 ActionDetector 邏輯
```

---

## 4. 動態熱載入與註冊流程
1. **目錄掃描**：系統啟動時，`backend/core/action_engine.py` 會自動掃描 `skills/*/config.json` 並動態加載。
2. **參數配置**：系統會自動將 `default_preferences` 注入全局設定。
3. **前端控制**：`/api/skills` 介面允許動態開啟/關閉技能、修改規則與事件邏輯。
