# RenUniversal 次世代智慧姿態監控代理系統：精確技術規範與架構說明

本文件提供 RenUniversal 專案的系統拓撲、核心演算法以及動態規則引擎的完整技術導覽，適用於系統架駕者與研發人員。

---

## 1. 系統拓撲與資料流 (System Topology)

RenUniversal 採用單向數據流與邊緣運算設計，整體系統由以下三個核心層級構成：

```mermaid
graph TD
    A[攝像頭輸入: 本地鏡頭 / 手機網路串流] -->|30 FPS MJPEG| B[Agent Pipeline 採樣層]
    B -->|影像關鍵點特徵提取| C[Shared State 狀態隔離層]
    B -->|物理幾何量測特徵| D[Action Judgment Engine 判定引擎]
    D -->|掃描與熱載入| E[Skills 動作判斷模組]
    D -->|姿態異常狀態判定| C
    C -->|狀態同步與快照| F[Flask/Web 渲染與串流服務]
    F -->|RESTful / Server-Sent Events| G[Next-Gen 網頁監控儀表板]
```

### 1.1 執行生命週期 (Lifecycle Sequence)

```mermaid
sequenceDiagram
    autonumber
    participant Client as 瀏覽器/儀表板
    participant Server as Stream Server
    participant Pipeline as Agent Pipeline
    participant Camera as VideoCaptureService
    participant Engine as ActionEngine
    participant State as SharedState

    Note over Pipeline, Camera: 伺服器啟動，初始化捕獲線程
    Pipeline->>Camera: 建立串流 (Local/Phone)
    loop 每秒 30 次循環 (30Hz)
        Camera->>Pipeline: 返回原始影像影格 (Raw Frame)
        Pipeline->>Pipeline: MediaPipe 關鍵點估算 (Face & Pose)
        Pipeline->>Pipeline: 計算物理幾何特徵向量
        Pipeline->>Engine: 送入姿態評估集 (Evaluate features)
        Engine->>Engine: 動態比對 rules.json 門檻規則
        Engine->>State: 更新當前異常狀態 (Ratio, Latency, Flags)
        Pipeline->>State: 更新最新標註影格 (Annotated Frame)
    end

    loop 輪詢狀態
        Client->>Server: GET /status
        Server->>State: 讀取當前狀態數據
        State-->>Client: 返回 JSON 狀態數據
    end
```

---

## 2. 幾何演算法與物理特徵提取 (Feature Extraction & Math Formulas)

核心幾何計算由 `backend/core/pipeline.py` 完成。系統提取以下特徵向量以判定坐姿健康度：

### 2.1 低頭比例 (Nose-Chin Ratio)
低頭判定基於 3D 面部網格在投影面上的長度變化。當頭部前傾時，鼻尖（Landmark 4）與下巴底端（Landmark 152）在影像上的垂直距離會縮短：
$$\Delta d_{\text{nose-chin}} = y_{\text{chin}} - y_{\text{nose}}$$
$$\text{Ratio} = \frac{\Delta d_{\text{nose-chin}} - d_{\text{baseline}}}{d_{\text{baseline}}}$$
*   **物理特性**：低頭時比率為負值（如 $-0.20$ 代表相較基準縮短了 20%）。

### 2.2 軀幹搖晃比 (Torso Sway)
軀幹的水平偏移以肩膀中點相對於影像寬度的偏離值來衡量。設左右肩膀頂點分別為 $S_L$ 與 $S_R$，其中心點為 $C_S = \frac{S_L + S_R}{2}$：
$$\text{Sway} = \frac{|x_{C_S} - x_{\text{baseline}}|}{W_{\text{frame}}}$$
*   **物理特性**：值恆大於或等於 0，偏離基準越遠數值越高。

### 2.3 軀幹前傾比 (Torso Lean)
軀幹前傾程度藉由雙肩中點與雙髖中點在垂直軸上的相對縮減比率來推估：
$$\text{Torso Length} = y_{\text{hips}} - y_{\text{shoulders}}$$
$$\text{Lean} = \frac{\text{Torso Length}_{\text{baseline}} - \text{Torso Length}}{\text{Torso Length}_{\text{baseline}}}$$

### 2.4 肩部傾斜度 (Shoulder Slope)
肩膀的倾角（Roll）透過計算雙肩連線斜率得出：
$$\text{Slope} = \frac{y_{S_R} - y_{S_L}}{x_{S_R} - x_{S_L}}$$

---

## 3. 動態規則引擎與視覺化幾何判定 (Action Engine & Geometric Rules)

### 3.1 插件式掃描與熱載入 (Python Backend)
Python 伺服器端提供一個動態插件載入器，能夠在免重啟服務的前提下重載判定規則：
*   **掃描路徑**：`skills/` 目錄。
*   **支援特徵字串**：`nose_chin_ratio`, `torso_sway`, `torso_lean`, `shoulder_slope`, `yaw_deviation`。

### 3.2 視覺化拓樸選點與物理層級判定 (iOS Native)
iOS 原生端拋棄了傳統的命名變數，採用全新的**「視覺化特徵對應 (Visual Topology Point Selection)」**與**「螢幕物理對齊」**：
*   **點位宣告**：使用者透過雙指縮放，直接從 500+ 個面部與身體節點中指定任意兩點 (如 `p11`, `p12` 雙肩，或 `f4`, `f152` 鼻尖下巴)。
*   **物理空間精準計算**：`RuleEngine.swift` 會將特徵的 Normalized 座標轉換為符合手機螢幕長寬比的物理像素幾何距離，避免因設備比例差異造成的橢圓誤差。

### 3.3 新世代幾何運算元 (Next-Gen Operators)
無論是 iOS 或 Web 介面，新版引擎支援以下高級幾何運算，直接處理點與點之間的空間變化：
*   **變長 / 變短 (`>`, `<`)**：計算任意兩點間距離是否大於或小於校準基準值的特定百分比或像素值。
*   **產生改變 (`><`)**：動態位移檢測。只要兩點間的距離相較於校準時「變長或變短」超過閥值，即觸發。
*   **超出範圍 (`~~`)**：**雙獨立球體越界檢測**。系統不再以線段長度判斷，而是記住兩點在校準時的「絕對空間座標」，並以該座標為中心畫出物理級別的正圓形防護網。只要任一端點飄出自己的防護圈，瞬間觸發。這完美解決了代償動作（例如頭沒歪，但整個身體平移）的防守死角。

---

## 4. 代碼映射與設計模式 (Implementation Map)

### 4.1 Python Backend 核心組件
| 原始碼檔案 | 責任範疇 | 使用之設計模式 |
| :--- | :--- | :--- |
| `backend/core/pipeline.py` | 核心流水線驅動、影像特徵提取 | **Pipeline Pattern** |
| `backend/core/action_engine.py`| 動態發現與載入 `/skills/` 動作包 | **Plugin Pattern** |
| `backend/core/state.py` | 線程安全的狀態同步、持久化讀寫 | **State Pattern** |

### 4.2 iOS Native 核心組件 (Swift)
| 原始碼檔案 | 責任範疇 | 使用之設計模式 |
| :--- | :--- | :--- |
| `MediaPipeService.swift` | 封裝 Google MediaPipe Tasks Vision C++ | **Adapter Pattern** |
| `RuleEngine.swift` | 處理 `~~`, `><` 等進階空間幾何運算與長寬比修正 | **Strategy Pattern** |
| `OverlayView.swift` | 根據幾何引擎結果，即時繪製完美的紅色/綠色防護圈與連線 | **Observer Pattern** |
| `PointReferenceView.swift` | 視覺化拓樸點位雙指縮放與拖曳選擇器 | **Interactive View Component** |

---

## 5. 開發者偵錯與驗證 (Verification Guide)

### 5.1 測試套件執行
我們提供架構合規性測試：
```bash
make test
```
該指令會觸發 `backend/test_architecture.py`，驗證當前核心 Skill 組件是否正確實作 Typed I/O 與 Pydantic 結構定義。
