# skills/ — 動作判斷包目錄

本目錄存放所有動作與姿態偵測模組（Skills）。系統底層偵測核心（`ActionEngine`）採用動態插件模式，於運行時自動掃描、載入並執行此目錄下每個子資料夾中的判斷包。

```text
skills/
└── <your_skill_name>/
    ├── config.json   # 必要：宣告規則、描述與預設配置
    └── logic.py      # 選用：自訂判定邏輯（省略時自動套用通用幾何偵測器）
```

📖 **完整開發指南已移至文件中心：**

- [動作判斷包開發 (Skills Development)](../docs/skills-development.md) — 目錄結構、`config.json` 規範、`logic.py` 進階實作
- [規則語法參考 (Rule Engine Reference)](../docs/rule-engine.md) — 點位、運算子與事件組合
