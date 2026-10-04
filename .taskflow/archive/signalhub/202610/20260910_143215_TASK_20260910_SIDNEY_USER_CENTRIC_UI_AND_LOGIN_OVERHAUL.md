# 任務：TASK_20260910_SIDNEY_USER_CENTRIC_UI_AND_LOGIN_OVERHAUL

**派發時間**：2026-09-10 14:35  
**優先級**：critical  
**負責人**：sidney (SignalHub)

---

## 📋 任務背景與總體方向
HQ 針對 SignalHub 全站進行了「用戶營運視角 vs 開發者視角」與「商業商務禮儀」的深度審核。
本系統是面向**機台主、場館店長與營運商**的商業產品，而不是工程師的自嗨工具；且商務對接面對邱先生（設備夥伴）、侯先生（遊戲系統商），全站嚴禁出現內部調侃暱稱。請立即依以下要求全面整改上線。

---

## 🛠️ 具體整改項目清單

### 1. 登入頁面重構與密碼顯示切換（/login）
- **修改檔案**：`PROJECT/SignalHub/resources/views/signal/auth/login-simple.blade.php`（及 `login.blade.php`）
- **密碼顯示切換（核心需求）**：
  - 在密碼輸入框右側增加 👁️ / 👁️‍🗨️ 切換按鈕（支援 Alpine.js 或原生 JS），點擊可在 `type="password"` 與 `type="text"` 之間無縫切換，方便用戶確認輸入。
- **品牌視覺統一**：
  - 徹底捨棄原先突兀的 `bg-gray-900` 與藍色按鈕，統一為 SignalHub 的暗黑科技風格（`bg-slate-900`、輸入框 `bg-slate-800 border-slate-700 focus:border-cyan-500`、按鈕 `bg-gradient-to-r from-cyan-500 to-cyan-400 text-slate-950 font-black`）。
  - 標題改為：**WAW SignalHub**，副標題：**智能機台信號中樞 (IoT Signal Management)**。
- **公開文檔入口**：
  - 登入卡片底部加入明顯連結：**「📘 遊戲商開洗分 API 介面規格書（免登入公開閱覽）」**（連向 `/signal-hub/guide`），方便合作方工程師直接查閱。

### 2. 用字遣詞與商務尊稱修正（徹底移除暱稱）
- **Profiles 設定精靈** (`resources/views/signal-hub/profiles.blade.php` 第 263 行)：
  - 將 `placeholder="例：老李1號機"` 修正為 **`placeholder="例：賽特1號機"`** 或 `例：VIP旗艦01號機`。
- **全站頁腳** (`resources/views/layouts/app.blade.php` 第 125 行)：
  - 移除括號內的內部 Agent 代號 `(Sidney)`！
  - 修正為：**`WAW Universal Signal Standard (WAW-USS) © 2026 WAW IoT System`**。
- **後端代碼註解** (`app/Http/Controllers/Api/V9/CallbackAckController.php` 第 12 行等)：
  - 清理「小猴」等非正式詞彙，修正為「遊戲開發商 / 合作系統端」。
  - 商務原則：面對邱先生（設備夥伴/供應商）、侯先生（遊戲開發商），全站嚴禁出現「老邱、小猴、老李」等私下簡稱。

### 3. 受眾視角翻轉（全面轉向用戶與業主視角）
- **頂部導航列優化** (`resources/views/layouts/app.blade.php`)：
  - **移除右上角 `[REST API]` 按鈕**（此為工程接口，對機台老闆是無效雜訊）。
  - 頁籤名稱生活化、業務化：
    - 原 `📡 設定檔` ➔ 更名為 **`📡 機台管理`**
    - 原 `⚡ 派送記錄` ➔ 更名為 **`⚡ 開洗分紀錄`**
    - 原 `🔔 Webhooks` ➔ 更名為 **`🔔 合作推送 (Webhooks)`**
    - 原 `🎛️ 模擬器` ➔ 更名為 **`🎛️ 機台測試`**
- **硬體黑話人話化**：
  - **模擬器** (`resources/views/signal-hub/simulator.blade.php`)：
    - 將「📥 採集輸入腳位 (PCNT 累加里程)」改為 **「📥 實體按鍵模擬 (開分 / 洗分)」**。
    - 將「點擊按鈕 = 現場光耦觸發」改為 **「點擊按鈕 = 模擬現場服務員按下實體鍵」**。
  - **腳位設定** (`resources/views/signal-hub/pins.blade.php`)：
    - 將「Relay / Open Drain」、「達林頓開路輸出」白話改為 **「繼電器開關輸出 / 電磁閥控制」**。
    - 運作模式增加易懂說明：「通知型（按一下觸發一次，如洗分）」、「計數型（連按累加，如開分）」。

### 4. 【重大業務補齊】開洗分紀錄增加「機台名稱」欄位
- **修改檔案**：`resources/views/signal-hub/deliveries.blade.php` 與關聯查詢（`SignalHubWebController` 或 API）
- **現狀問題**：目前表格只有「時間、腳位、發送值、回報點數...」，完全不知道是「哪一台機台」！業主有 10 台機台時無法對帳。
- **要求**：
  - 在「時間」後方新增 **「機台」** 欄位。
  - 顯示機台自訂名稱（例如：`賽特 #01` 或 profile 名稱），若無則顯示 Chip ID。

---

## 🚀 交付與驗收標準
1. 本地修改完成並經完整語法檢查後，提交 Git 並 Push 至 `origin main`。
2. 執行遠端部署 `../../dev_tools/waw_ops.sh deploy sidney`。
3. 遠端執行 `php artisan route:clear && php artisan view:clear`。
4. 驗證登入頁面（密碼眼睛圖示切換正常、導向規格書連結正常）。
5. 驗證開洗分紀錄表格已出現「機台」欄位。
6. 驗證全站無「老李、老邱、小猴、(Sidney)、REST API」等雜訊。
7. 依標準格式提交回報至 `.taskflow/signalhub/outbox/`。

