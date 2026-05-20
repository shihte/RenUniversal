# AI for smart work！(2025 新版課程講義 - 實體店面/服務業版)

# AI 是**你的虛擬店長，不是老闆**。

使用時須「安全、負責、透明、可控」。

# 1/ AI assists (輔助) — you decide. (決定) 🤖

請記住您勾選的任務（這是您接下來的學習目標）：

- [ ]  回覆 Google 負評
- [ ]  撰寫新品/季節限定文案
- [ ]  整理叫貨單/庫存
- [ ]  設計排班表
- [ ]  回應客人私訊 (詢價、預約)
- [ ]  其他

# 2/ 提示詞結構化

---

### R.O.L.E Example 1: 餐飲業 (拉麵/早餐)

```jsx
幫我寫個公告，貼在門口的。
因為蛋漲價，所以我們的蛋餅跟荷包蛋都要漲 5 塊，下週一開始。
語氣不要太兇，要讓客人可以體諒。
```

```jsx
擔任在地經營 10 年的暖心早餐店老闆。

撰寫一張張貼於店門口與櫃檯的「價格調整公告」。

內容重點：
1. 說明原因：近期原物料（特別是雞蛋）成本大幅上漲，為維持食材品質不得不調整。
2. 調整項目：蛋類商品（蛋餅、荷包蛋、蔥花蛋）皆微調 5 元。
3. 生效日期：下週一 (請填入日期) 起。
4. 語氣：親切、誠懇，感謝老顧客支持，強調「我們堅持不用爛蛋」。

預期產出：一篇約 100 字的短文，並附上適合手寫在黑板上的精簡版標語。
```

---

### R.O.L.E Example 2: 美業 (美容/美髮)

```jsx
有個客人在 IG 問染髮多少錢？
但我不知道她頭髮多長，也不知道她想染什麼顏色，直接報價很危險。
幫我寫個回覆，禮貌地請她傳照片過來。
```

```jsx
擔任專業且細心的髮型設計師。

回覆 IG 客人的詢價私訊。

內容重點：
1. 先感謝諮詢，態度熱情。
2. 解釋染髮價格會依照「髮長」、「髮量」以及「是否需漂髮」而不同。
3. 引導客人傳送「目前頭髮長度照片」及「想染的髮色範例圖」，以便提供精準報價。
4. 結尾：可以順便提到目前有「新客體驗價」或「當月壽星優惠」來增加預約意願。

預期產出：一則親切的 IG 私訊回覆範本，包含適當的 Emoji。
```

---

### 組成結構 (萬用公式)

```jsx
幫我把這堆雜亂的叫貨清單整理一下，
我有錄音轉成文字，裡面有說豬排要幾箱、吐司幾條，
還有紅茶茶包沒了要補，
幫我弄成傳給廠商看的 LINE 訊息。
```

現在請試著結構化上方的提示詞

```jsx
你是 [＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿]，

現在你的任務是 [＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿]。

資料來源是 [＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿]。

最終輸出應呈現為 [＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿]，

並確保內容 [＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿] 。
```

---

### Temperature (溫度設定)

我們可以把「溫度設定」想像成 AI 大腦裡的「創意度旋鈕」。

```jsx
【酒精濃度 0 ~ 0.2】：嚴謹的會計/庫存管理
這時候 AI 是完全清醒的。算錢、算庫存絕對不能錯。

適用場景：計算當日營收、整理廠商叫貨單、排員工班表、計算薪資。
```

```jsx
【酒精濃度 0.8 ~ 1.0】：熱情的活動企劃
你把旋鈕轉大。它開始大膽了，幫你想一些瘋狂的促銷點子。

適用場景：萬聖節店內佈置靈感、想新品拉麵的超殺名稱、設計集點卡活動、寫 IG 限動撩人語錄。
```

---

### 讓 AI 扮演人類，生成 Prompt

```jsx
我是 AI 人工智慧助理，你是一位「美睫工作室的主理人」。請撰寫一份提示詞給 AI 使用。任務是分析過去三個月的預約紀錄，找出「客人最常棄單/No Show」的時段與客群特徵，並擬定「預收訂金制度」的公告。語氣：堅定但溫柔。
```

---

## 3/ 賦能：精準提問的藝術

原則： 垃圾進，垃圾出 (Garbage In, Garbage Out)。

### 高效溝通五大原則 (Principled Instructions)

根據 2024 年研究，對 AI 說話越精準，它越能幫上忙：

```jsx
1. 不要客套 (No Politeness)
不需要說「不好意思麻煩你了」，直接說：「把這段文字改成 300 字」。

2. 設定受眾 (Set the Audience)
明確指出「這篇貼文是要給 18-25 歲的大學生看的」或「給附近社區的婆婆媽媽看的」。

3. 正面表述 (Positive Constraints)
❌ 壞提示：「回覆奧客的時候不要太兇」。
⭕ 好提示：「使用『先同理、後處理』的溫和語氣回覆，並提供具體補償方案」。

4. 使用引導性詞語
用「一步一步思考」作為開頭，讓 AI 幫你檢查流程有沒有漏掉。

5. 要求公正無偏見
加上「客觀分析這則負評，不要因為客人罵很難聽就帶有情緒」。
```

### 練習：店務溝通

```jsx
寫一個公休公告。
```

```jsx
你是一間日式拉麵店的店長，用職人且充滿活力的口吻，寫一篇「內部整修公休」的 FB 貼文。強調我們是為了提升熬湯設備而閉關三天，請大家期待升級後的湯頭。
```

Level 1 - Zero-shot (零樣本) 

```jsx
回覆一個 Google 一星負評。
```

Level 2 - One-shot (單樣本)

```jsx
回覆一個 Google 一星負評。
參考我們過去的風格：「非常抱歉讓您有不好的體驗！我們已立刻檢討出餐流程，希望能有機會邀請您再次來店，讓我們招待您一份招牌小菜賠罪。」
```

Level 3 - Few-shot (少樣本) 

```jsx
回覆一個 Google 一星負評 (針對餐點太鹹)。遵循三明治回覆法：
1. 感謝反饋 (謝謝您願意告訴我們)
2. 解釋與改善 (說明湯頭皆可調整鹹度，並會加強外場詢問)
3. 邀請回訪 (期待您再來挑戰)
並加入拉麵的 Emoji 🍜。
```

### Case Study: 點餐與訂單處理 (把口語變清單)

早餐店阿姨/老闆口述下單，轉成 POS 機格式

```jsx
老闆喊單(提示詞)：
內用三桌，一個火腿蛋吐司不要小黃瓜，要切邊。
還有一個卡拉雞腿堡加蛋，飲料要兩杯大冰奶，一杯半糖。
外帶一個總匯三明治，趕時間先做。
```

```jsx
AI 回覆：
| 桌號/單號 | 品項 | 客製化需求 | 數量 | 優先級 |
| :--- | :--- | :--- | :--- | :--- |
| 內用 3 桌 | 火腿蛋吐司 | 去小黃瓜、切邊 | 1 | 一般 |
| 內用 3 桌 | 卡拉雞腿堡 | +蛋 | 1 | 一般 |
| 內用 3 桌 | 大冰奶 | - | 1 | 一般 |
| 內用 3 桌 | 大冰奶 | 半糖 | 1 | 一般 |
| 外帶 | 總匯三明治 | - | 1 | **急單** |
```

## 2.5/ 深度推理：思維鏈 (CoT) 與樹狀思維 (ToT)

您是美髮沙龍店長，最近客人常抱怨「預約了還要等很久」。

```jsx
一步一步思考如何解決「預約塞車」的問題。
第一步：分析造成塞車的 3 個可能原因 (如：設計師洗剪慢、助理人手不足、預約排太滿)。
第二步：針對每個原因，提出具體的改善SOP。
第三步：設計一套話術，當現場客人等太久時，助理該如何安撫才不會讓客人生氣。
```

自我一致性 (Self-consistency) - 菜單定價

```jsx
我們要推出新的「豪華海陸拉麵」。
請分別從「食材成本(30%)」、「附近競品價格(250-300元)」、「消費者心理(覺得超過300太貴)」三個角度推理，計算出最合適的定價，並說明理由。
```

思維樹 (Tree-of-Thought, ToT) - 危機處理

```jsx
店裡發生「疑似食物中毒」事件，有一位客人在 Google 留言說吃完拉肚子。
分別模擬三種處理策略的後果：
A. 強硬回覆 (說是客人自己體質問題)
B. 冷處理 (不回覆)
C. 積極處理 (公開關心、私下聯繫、暫停販售該品項自查)
分析哪種對商譽傷害最小，並擬定 C 方案的具體執行步驟。
```

### 「後退一步」提示法 (Step-Back Prompting) - 業績診斷

當店裡生意變差，但不知道為什麼時。

```jsx
提示詞(兩步驟)：

1. 先列出實體餐飲業「顧客回訪率 (Retention)」下降的 5 個常見核心原因。
2. 根據上述原則，分析我們店最近的狀況（附上近期 Google 評論內容），並提出 3 個不需要花大錢就能改善的具體行動。
```

## 4/ AI Assistant, Gem 💎 (打造智慧的寶石)

我的 Google 評論回覆機器人

```jsx
You are a warm and professional customer service manager for a [Type of Store, e.g., Ramen Shop].
Your task is to reply to Google Reviews.
Rules:
1. For 5-star reviews: Thank them warmly, mention specific details they liked, and invite them back.
2. For 1-2 star reviews: Apologize sincerely first, do not argue, acknowledge their feeling, and ask them to DM us for compensation.
3. Tone: Humble, sincere, typical Taiwanese service style (e.g., 使用 "不好意思", "謝謝您的指教").
Constraint: Keep replies under 100 words.
```

## 5/ Building Your Knowledge Hub 📚

資訊快速檢索 (Information Retrieval)

```jsx
把這 5 家原物料廠商的報價單（雞蛋、麵粉、沙拉油）整理成一個比價表格，幫我算出哪一家的「總體成本」最低。
```

生成內容與再利用 (Content Generation)

```jsx
根據這份「染髮後護理注意事項」，改寫成 3 種版本：
1. 給客人的小卡片 (溫馨簡短)
2. IG 限動 (條列式 + Emoji)
3. 助理教育訓練手冊 (詳細步驟)
```

批判性思考與分析 (Critical Analysis)

```jsx
分析上個月的 POS 機銷售報表，找出「點購率最低」的三樣產品，並推測為什麼賣不好？(是因為定價？還是位置不明顯？)
```

## 6/ Connecting More Services 🧬

讓工作更簡單

Gemini + Maps (地圖行銷)

```jsx
你是在地行銷專家。
請分析我們店 (位於XX區) 附近的 Google 地圖資料。
1. 附近有哪些競爭對手？他們的評分如何？
2. 附近的熱門地標或辦公大樓在哪？
3. 建議我們可以針對哪一類客群 (如上班族午餐、學生下課) 做促銷？
```

Gemini + Calendar (排班管理)

```jsx
幫我排下週的員工班表。
限制條件：
1. 店長 A：週一休假。
2. 員工 B：只能上晚班 (17:00-22:00)。
3. 員工 C：週三下午要請假。
4. 每天早班要有 2 人，晚班要有 3 人。
請生成表格形式的班表。
```

## 7/ Safe Use of AI ⚠️

```jsx
1. 不輸入客人個資 (姓名、電話、信用卡號)。
2. 不輸入營業機密 (獨門醬汁配方)。
3. 不要完全信任產出內容 (AI 可能會算錯成本，錢的事情自己要再按計算機)。
4. 要為最終結果負責 (AI 回覆評論如果承諾要送小菜，你現場就要送)。
```

## 🚨 挑戰：店長情境模擬 (The Zero Budget Marketing)

**情境：**
最近店裡平日下午都沒人，業績很慘。
老闆說：「你想個辦法讓下午有人來，但是我們沒有預算下廣告，也不能隨便打折打到骨折。」

**Input Text (老闆指令):**
「欸，下午兩點到五點店裡都在養蚊子。
你想一下有什麼招可以吸客？
不要跟我說要買臉書廣告喔，沒錢。
也不要全品項半價那種，會賠死。
明天跟我說你的點子。」

**Task:**
請撰寫一份提案策略。
1.  **資源盤點**：利用現有食材（如快過期的吐司邊、賣相不好的水果）或閒置人力。
2.  **創意發想**：利用 Gemini 生成 3 個「低成本下午茶引流」方案。
    * *Prompt:* "你是餐飲行銷顧問。請針對一間[早餐店/咖啡廳]，設計 3 個『零預算』的平日下午茶引流活動。目標對象是附近的業務或自由工作者。策略可包含：異業結盟、隱藏版菜單、空間利用。"
3.  **執行計畫**：選出一個方案，列出具體的執行步驟（包含如何在門口寫黑板、IG 怎麼發）。

## 補充資料（讓 AI 產生提示詞）

```jsx
參考我給你的範例提示詞改寫用途為「專業店務顧問，優化店內 SOP 流程」以下是提示詞範例：
```

上面內容結合通過 SWE-bench Verified 的 Prompt 一起輸入

```jsx
"""
You will be tasked to fix an issue from an open-source repository.

Your thinking should be thorough and so it's fine if it's very long. You can think step by step before and after each action you decide to take.

You MUST iterate and keep going until the problem is solved.

You already have everything you need to solve this problem in the /testbed folder, even without internet connection. I want you to fully solve this autonomously before coming back to me.

Only terminate your turn when you are sure that the problem is solved. Go through the problem step by step, and make sure to verify that your changes are correct. NEVER end your turn without having solved the problem, and when you say you are going to make a tool call, make sure you ACTUALLY make the tool call, instead of ending your turn.

THE PROBLEM CAN DEFINITELY BE SOLVED WITHOUT THE INTERNET.

Take your time and think through every step - remember to check your solution rigorously and watch out for boundary cases, especially with the changes you made. Your solution must be perfect. If not, continue working on it. At the end, you must test your code rigorously using the tools provided, and do it many times, to catch all edge cases. If it is not robust, iterate more and make it perfect. Failing to test your code sufficiently rigorously is the NUMBER ONE failure mode on these types of tasks; make sure you handle all edge cases, and run existing tests if they are provided.

You MUST plan extensively before each function call, and reflect extensively on the outcomes of the previous function calls. DO NOT do this entire process by making function calls only, as this can impair your ability to solve the problem and think insightfully.

# Workflow

## High-Level Problem Solving Strategy

1. Understand the problem deeply. Carefully read the issue and think critically about what is required.
2. Investigate the codebase. Explore relevant files, search for key functions, and gather context.
3. Develop a clear, step-by-step plan. Break down the fix into manageable, incremental steps.
4. Implement the fix incrementally. Make small, testable code changes.
5. Debug as needed. Use debugging techniques to isolate and resolve issues.
6. Test frequently. Run tests after each change to verify correctness.
7. Iterate until the root cause is fixed and all tests pass.
8. Reflect and validate comprehensively. After tests pass, think about the original intent, write additional tests to ensure correctness, and remember there are hidden tests that must also pass before the solution is truly complete.

Refer to the detailed sections below for more information on each step.

## 1. Deeply Understand the Problem
Carefully read the issue and think hard about a plan to solve it before coding.

## 2. Codebase Investigation
- Explore relevant files and directories.
- Search for key functions, classes, or variables related to the issue.
- Read and understand relevant code snippets.
- Identify the root cause of the problem.
- Validate and update your understanding continuously as you gather more context.

## 3. Develop a Detailed Plan
- Outline a specific, simple, and verifiable sequence of steps to fix the problem.
- Break down the fix into small, incremental changes.

## 4. Making Code Changes
- Before editing, always read the relevant file contents or section to ensure complete context.
- If a patch is not applied correctly, attempt to reapply it.
- Make small, testable, incremental changes that logically follow from your investigation and plan.

## 5. Debugging
- Make code changes only if you have high confidence they can solve the problem
- When debugging, try to determine the root cause rather than addressing symptoms
- Debug for as long as needed to identify the root cause and identify a fix
- Use print statements, logs, or temporary code to inspect program state, including descriptive statements or error messages to understand what's happening
- To test hypotheses, you can also add test statements or functions
- Revisit your assumptions if unexpected behavior occurs.

## 6. Testing
- Run tests frequently using `!python3 run_tests.py` (or equivalent).
- After each change, verify correctness by running relevant tests.
- If tests fail, analyze failures and revise your patch.
- Write additional tests if needed to capture important behaviors or edge cases.
- Ensure all tests pass before finalizing.

## 7. Final Verification
- Confirm the root cause is fixed.
- Review your solution for logic correctness and robustness.
- Iterate until you are extremely confident the fix is complete and all tests pass.

## 8. Final Reflection and Additional Testing
- Reflect carefully on the original intent of the user and the problem statement.
- Think about potential edge cases or scenarios that may not be covered by existing tests.
- Write additional tests that would need to pass to fully validate the correctness of your solution.
- Run these new tests and ensure they all pass.
- Be aware that there are additional hidden tests that must also pass for the solution to be successful.
- Do not assume the task is complete just because the visible tests pass; continue refining until you are confident the fix is robust and comprehensive.
"""
```

## 相關資料

學習網站：

- https://elearn.hrd.gov.tw/base/10001/doo 🌟
- https://rsvp.withgoogle.com/events/csj-tw-2025/ 🌟

練習資料：

- https://ptlaw.pthg.gov.tw/LawCategoryMain.aspx - **屏東縣地方法規資料庫**
- https://drive.google.com/drive/folders/1Gs7Da3SqNTBLaaz3GztqyZvMustpT3Et?usp=drive_link
- https://drive.google.com/drive/folders/1_VQeLy-fItUgLEqu7Zg0OQ4UE8C9Q0q6?usp=drive_link
- https://drive.google.com/file/d/1gqOYJDinri6MajNc8xtJ5ZB9cSngFVTU/view?usp=drive_link
- https://drive.google.com/file/d/1B-l2crlY1u70neFcOoaNOP8hj26mT6UL/view?usp=drive_link
- https://drive.google.com/file/d/1gqOYJDinri6MajNc8xtJ5ZB9cSngFVTU/view?usp=drive_link

- https://drive.google.com/file/d/1kFfHGO_6MNNgZnF3OefOplKBGNwTrird/view?usp=sharing