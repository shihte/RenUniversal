# 📱 RenUniversal iOS 原生應用：超越網頁版的極致體驗

> 回到 [文件中心](README.md)

RenUniversal 起初是作為一個 Web/Python 架構的專案，但為了解決網頁版在影像傳輸與運算上的瓶頸，我們打造了這個**全原生的 iOS 應用程式**。

這不僅僅是一個附屬工具，而是一個**完全超越網頁版體驗、效能與操作直覺性的終極型態**。

---

## 📥 立即下載 (Direct Install)

為了實現我們「零門檻阿公級臨床部署」的初衷，我們準備了無殼 (DRM-Free) 的越獄/側載直裝版 IPA 檔案：

👉 **[下載 RenUniversal iOS 1.3.1 (無殼版 IPA)](../releases/RenUniversal_v1.3.1_iOS.ipa)** *(大小約 19MB)*

> 🛡️ **安全與防偽驗證 (Anti-Tampering Hash)**
> 為避免有心人士二次打包植入惡意程式碼（釣魚或木馬），請在下載後核對檔案的唯一哈希值（SHA-256 Checksum）：
> `10a0db7798f6c239a3ad36ea0dc7da236670abfeae9ab5d8e1b7dd3f967ea89b`

### 安裝方式 (無須 Mac)
若您沒有 Mac 電腦，可以透過以下任一主流側載工具將 App 安裝至您的 iPhone/iPad：
*   **[TrollStore](https://trollstore.app/)** (推薦：永久簽名免越獄)
*   **[AltStore](https://altstore.io/)** / **[SideStore](https://sidestore.io/)** (需每 7 天重簽)
*   **[Sideloadly](https://sideloadly.io/)** (支援 Windows / Mac 簽名部署)

---

## 🚀 為什麼 iOS 原生版比網頁版更好？

### 1. 效能的絕對輾壓 (Apple Neural Engine)
網頁版受限於瀏覽器的 WebGL/WASM 效能，且常需要透過 Wi-Fi 傳輸高解析度影像到電腦端處理，延遲難以避免。
iOS 原生版直接底層整合 **Google MediaPipe C++ 核心與 Swift Wrapper**，100% 榨乾 iPhone/iPad 內建的 **Apple Neural Engine (神經網路引擎)**。
*   **零網路延遲**：完全不需要連線至電腦端的 Python 伺服器，所有運算在手機本機端光速完成。
*   **60 FPS 滿血運行**：骨架與臉部捕捉極度滑順，發熱量極低。

### 2. 革命性的視覺化「拓樸點位」選擇系統
在網頁版中，你要設定一個新的判定規則，可能需要去查表找點位代號（如 `f1`, `p11`）。
在 iOS 原生版，我們開發了**「PointReferenceView 視覺化選擇器」**：
*   **雙指縮放與拖曳**：如同操作 Apple Maps 一樣，你可以將人臉或身體骨架無限放大。
*   **直覺點擊**：直接用手指點選畫布上的 500+ 個特徵節點，系統會精準捕捉並綁定你的選擇。完全告別查表盲猜的時代。

### 3. 完美對齊物理像素的「動態幾何引擎」
網頁版的幾何判定在某些特殊長寬比的手機上，容易產生視覺與數學邏輯不匹配的誤差。
iOS 原生版的 **`RuleEngine` 幾何引擎經過了最高級別的重構**：
*   **自動消除長寬比誤差**：無論你是用細長的 iPhone X 或是平板 iPad，數學防護圈都會精準對齊物理螢幕。
*   **雙獨立球體越界檢測 (`~~`)**：獨創的越界偵測模式。不再只是計算兩點間的距離，而是為這兩個點各自畫出「專屬的防護圈」，只要有任何一個點飄出自己的圈圈，瞬間飆紅觸發，完美解決了代償動作難以捕捉的問題。

### 4. Apple-Style 極致介面與硬體級隱私防護
*   **原生 SwiftUI 介面**：半透明毛玻璃 (Glassmorphism)、順滑的彈出視窗、即時的高光與陰影動畫，帶來極致尊榮的使用者體驗。
*   **底層臉部抹除**：iOS 版的臉部打碼是在相機影像串流的**最底層**進行處理。它會精準計算頭部輪廓並向外延伸 150%，覆蓋五官、耳朵甚至頭髮邊緣，保障絕對隱私的同時，**完全不干擾底層的 AI 點位捕捉**。

### 5. 零門檻的「阿公級」臨床部署體驗 (Ultimate Elder-Friendliness)
這是開發原生 App 最核心、也是最重要的初衷：**「需要復健的長輩，不可能會開終端機下 `make build` 指令。」**
過去的網頁/Python 版雖然架構強大，但部署門檻極高，不適合直接發放給居家的病患。
而現在的 iOS 原生版，將所有複雜的 AI 運算、幾何模型與事件判定，全部封裝成一個小小的 App Icon。
**阿公阿嬤只需要「點擊 App、對準鏡頭」，就能立刻開始 CTAR 復健並獲得最專業的姿態回饋。** 臨床醫師與家屬終於能真正做到「一鍵無痛部署」。

---

## 🛠 如何編譯與部署

因為這是一個開源的開發者專案，您可以直接透過 Xcode 將其編譯並安裝到您的實體設備上：

### 準備工作
1. 一台 Mac 電腦。
2. 安裝最新版的 [Xcode](https://developer.apple.com/xcode/)。
3. 一部執行 **iOS 15.0 或以上** 的 iPhone 或 iPad 與傳輸線。

### 步驟
1. 開啟終端機，克隆專案（若已克隆請忽略）：
   ```bash
   git clone https://github.com/shihte/RenUniversal.git
   cd RenUniversal/RenUniversal
   ```
2. **非常重要**：請點擊開啟 **`RenUniversal.xcworkspace`** 檔案（**請勿**開啟 `.xcodeproj`，因為我們使用了 CocoaPods 管理 MediaPipe 依賴）。
3. 在 Xcode 左側導覽列點選最上方的 `RenUniversal` 專案。
4. 進入 `Signing & Capabilities` 標籤頁：
   * 勾選 `Automatically manage signing`。
   * 在 `Team` 下拉選單中，登入並選擇你的 Apple ID。
   * *（如果 Bundle Identifier 報錯，請在後面加上隨機英數字如 `com.yourname.RenUniversal`）*
5. 將你的 iPhone 解鎖並接上電腦。在 Xcode 頂部正中央的裝置列表選取你的 iPhone。
6. 點擊左上角的 **「▶ 播放鍵 (Build and Run)」**。
7. 第一次安裝時，iPhone 會顯示「不受信任的開發者」。請至 iPhone 的 `設定 -> 一般 -> VPN與裝置管理` 中信任你的 Apple ID。
8. 再次點擊 App，享受極致順暢的姿態監控體驗！

---

## 📝 版本更新紀錄 (Changelog)

### v1.3.1 (Current)
*   **[新功能] 歪頭偵測 (Tilt Skill)**：新增對 y 軸絕對距離放大的支援，自動連動 bad_posture 事件。
*   **[新功能] x/y 軸距離標示線**：當使用軸向距離運算子（如 `y<>`）時，畫面會精準畫出水平或垂直的距離標示線。
*   **[狀態同步] 舊裝置熱更新**：安裝新版的裝置會在啟動後，自動幫使用者的舊狀態補齊 tilt Skill 並更新 bad_posture 規則。

### v1.0.1
*   **[相容性升級]**：徹底解除 iOS 17 的版本鎖定，全面向下相容至 **iOS 15.0**，支援更多舊款裝置（如 iPhone 6s / 初代 SE 等）。
*   **[幾何引擎修復]**：修正了 `~~` (超出範圍) 在不同長寬比螢幕上的變形問題，現在雙獨立球體已完美對齊螢幕的物理像素。
*   **[穩定性優化]**：修復了刪除事件或技能時導致 App 崩潰的記憶體與狀態同步錯誤。
*   **[介面優化]**：修復了第一次點擊「編輯」按鈕時內容顯示為空的問題；更新了全新專屬的 `R_Logo` 應用程式圖示。
