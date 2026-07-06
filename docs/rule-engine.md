# 📐 規則語法參考 (Rule Engine Reference)

RenUniversal 的姿態判定建立在一套簡潔的幾何規則語法上。本文件是該語法的**權威參考**，內容對應後端解析器 [`generic_skill_detector.py`](../backend/core/generic_skill_detector.py) 與事件引擎 [`event_engine.py`](../backend/core/event_engine.py) 的實際行為。

> 回到 [文件中心](README.md)

---

## 1. 概念分層：技能 (Skill) 與事件 (Event)

| 層級 | 角色 | 範例 |
| :--- | :--- | :--- |
| **技能 Skill** | 底層幾何特徵判定，輸出單一布林狀態 | `f1,f152 >< num=20%`（低頭） |
| **事件 Event** | 將多個技能／特徵以邏輯運算組合成高階語意 | `lean OR turn`（代償動作） |

技能存放於 `skills/`，事件存放於 `events/`，皆以 `config.json` 的 `rule_syntax` 欄位描述規則。

---

## 2. 點位語法 (Point IDs)

每個點位指向一個 MediaPipe 特徵節點，格式為 `<前綴><索引>`：

| 寫法 | 意義 | 範例 |
| :--- | :--- | :--- |
| `f<n>` | **臉部** Face Mesh 地標（0–467） | `f1` 鼻尖、`f152` 下巴、`f33` 左眼、`f263` 右眼 |
| `p<n>` | **身體** Pose 骨架地標（0–32） | `p11` 左肩、`p12` 右肩 |
| `<n>` | 裸數字：≤ 32 視為身體，> 32 視為臉部 | `11` 等同 `p11` |

> 建議一律加上 `f` / `p` 前綴以避免歧義。

---

## 3. 幾何運算子 (Operators)

規則的核心形式為「**兩點之間**的距離相對於校準基準的變化」：

```text
[點位1],[點位2] [運算子] num=[數值][單位]
```

#### 相對距離運算子（比較兩點歐式距離）

| 運算子 | 名稱 | 觸發條件 |
| :---: | :--- | :--- |
| `><` | **縮短 Shrink** | 當前距離較基準**縮小**達指定比例 |
| `<>` | **放大 Expand** | 當前距離較基準**放大**達指定比例 |
| `>><< ` | **變化 Change** | 當前距離與基準的偏差**絕對值**達指定比例 |
| `~~` | **越界 Capsule** | 雙獨立球體越界檢測（見 §5） |

#### 軸向絕對距離運算子（v1.3.0+）

在運算子前加上軸向前綴 `x` 或 `y`，可只比較**單一軸向**的像素距離（不受校準基準影響）：

| 運算子 | 軸向 | 名稱 | 觸發條件 |
| :---: | :---: | :--- | :--- |
| `x><` | 水平 | **x 縮短** | 兩點水平距離 < 基準水平距離 × (1 - threshold) |
| `x<>` | 水平 | **x 放大** | 兩點水平距離 > 基準水平距離 × (1 + threshold) |
| `y><` | 垂直 | **y 縮短** | 兩點垂直距離 < 基準垂直距離 × (1 - threshold) |
| `y<>` | 垂直 | **y 放大** | 兩點垂直距離 > 基準垂直距離 × (1 + threshold) |

> ⚠️ 軸向運算子搭配 `num=Npx` 時為純絕對像素閾值（不比較基準）；搭配 `num=N%` 時以基準軸向距離為 100%。

#### UI 可視化標示線

觸發後 pipeline 和 iOS Overlay 會在畫面上自動標示線段：
- **`x` 前綴**：在兩點 y 座標中點畫**水平線**
- **`y` 前綴**：在兩點 x 座標中點畫**垂直線**
- **無前綴**：連接兩點的**斜線**
- 監控時為綠色，觸發時轉**紅色**

### 單位 (num)
| 寫法 | 意義 |
| :--- | :--- |
| `num=20%` | 相對基準變化 20% |
| `num=50px` | 絕對像素閾值（不受 slider 偏好覆寫） |

> 校準（Calibration）會記錄使用者初始 3 秒的基準距離 `d_base`；判定時以當前距離 `d_curr` 與其比較：`change = (d_curr - d_base) / d_base`。

---

## 4. 邏輯組合 (Logical Composition)

技能規則與事件規則都可用邏輯運算子串接多個子條件：

| 運算子 | 等義寫法 | 說明 |
| :--- | :--- | :--- |
| `AND` | `and` | 兩者皆成立 |
| `OR` | `or` | 任一成立 |
| `NOT` | `!` | 反相 |
| `( )` | — | 改變運算優先序 |

邏輯運算子**不分大小寫**。範例：

```text
f1,f152 >< num=20% AND p11,p12 ~~ num=40px
(lean OR turn) AND !slouch
```

> 🔒 **安全說明**：規則字串經解析後，子條件會被替換為 `True`/`False`，再交由 **AST 白名單布林求值器**（[`safe_eval.py`](../backend/core/safe_eval.py)）計算——僅允許 `True/False/and/or/not/括號`，任何函式呼叫、屬性存取或算術運算都會被拒絕，杜絕規則注入風險。詳見 [隱私保護與資安](privacy-and-security.md)。

---

## 5. `~~` 雙獨立球體越界檢測 (Capsule Detection)

`~~` 是專為**代償動作**設計的進階運算子。它不比較兩點「之間」的距離，而是記住兩點在校準時的**絕對空間座標**，並各自畫出一個半徑為 `num` 的防護圈。只要**任一端點飄出自己的防護圈**即觸發。

這解決了「頭沒歪、但整個身體平移」這類傳統線段長度判定抓不到的死角。

```text
p11,p12 ~~ num=40px
```

---

## 6. 完整範例

### 技能：歪頭偵測（`skills/tilt/config.json`，v1.3.0+）
```json
{
  "name": "tilt",
  "description": "歪頭檢測 (y軸絕對距離放大)",
  "enabled": true,
  "requirements": { "face_mesh": true, "pose": false },
  "rule_syntax": "f33,f263 y<> num=15px"
}
```

> `y<>` 比較兩眼（`f33` 左眼、`f263` 右眼）垂直方向距離——正常時兩眼幾乎等高（y 距離接近 0），歪頭時垂直差距增大。`num=15px` 為絕對像素閾值，畫面上以垂直線可視化。

### 技能：低頭偵測（`skills/slouch/config.json`）
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

### 事件：代償動作（`events/bad_posture/config.json`）
```json
{
  "name": "bad_posture",
  "description": "錯誤代償動作 (前傾、轉頭或歪頭)",
  "enabled": true,
  "rule_syntax": "lean OR turn OR tilt",
  "default_preferences": {}
}
```

---

## 7. 延伸閱讀

- 想將規則打包成可重用的技能、加上自訂 `logic.py`？見 [動作判斷包開發](skills-development.md)。
- 想了解距離正規化與幾何數學細節？見 [系統架構與演算法](DETAILED_ARCHITECTURE.md)。
