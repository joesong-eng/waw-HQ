# 任務回報：TASK_20260910_SIDNEY_USER_CENTRIC_UI_AND_LOGIN_OVERHAUL

**完成時間**：2026-09-10 15:00  
**執行者**：sidney (SignalHub)  
**任務依據**：`.taskflow/signalhub/inbox/20260910_143215_TASK_20260910_SIDNEY_USER_CENTRIC_UI_AND_LOGIN_OVERHAUL.md`  
**Git Commit**：`d73ebd4` (main)

---

## 執行成果清單

### 1. 登入頁面重構與密碼顯示切換（/login）
- **修改檔案**：
  - `PROJECT/SignalHub/resources/views/signal/auth/login-simple.blade.php`
  - `PROJECT/SignalHub/resources/views/signal/auth/login.blade.php`
- **實作內容**：
  - **密碼顯示切換**：在密碼輸入框右側增加 👁️ / 👁️‍🗨️ 切換按鈕（基於 Alpine.js `showPassword`），點擊可無縫切換 `type="password"` 與 `type="text"`，方便機台主與場館操作者確認輸入。
  - **品牌視覺統一**：徹底捨棄原先突兀的 `bg-gray-900` 與藍色按鈕，全面對齊 SignalHub 暗黑科技風（主體 `bg-slate-900`、卡片 `bg-slate-800/90 border-slate-700/80`、輸入框 `bg-slate-800 border-slate-700 focus:border-cyan-500`、主按鈕 `bg-gradient-to-r from-cyan-500 to-cyan-400 text-slate-950 font-black`）。
  - **品牌標題與副標**：標題設為 **WAW SignalHub**，副標題設為 **智能機台信號中樞 (IoT Signal Management)**。
  - **公開規格書入口**：於登入卡片底部加入高辨識度外框連結：**「📘 遊戲商開洗分 API 介面規格書（免登入公開閱覽）」**（直通 `/signal-hub/guide`），外部工程師可直接免登入閱覽規格。

### 2. 用字遣詞與商務尊稱修正（徹底清除內部暱稱）
- **Profiles 設定精靈** (`PROJECT/SignalHub/resources/views/signal-hub/profiles.blade.php` 第 263 行)：
  - 機台名稱範例由 `placeholder="例：老李1號機"` 修正為 **`placeholder="例：賽特1號機"`**。
- **全站頁腳** (`PROJECT/SignalHub/resources/views/layouts/app.blade.php`)：
  - 移除括號內的內部 Agent 代號 `(Sidney)`。
  - 修正為正式規格宣告：**`WAW Universal Signal Standard (WAW-USS) © 2026 WAW IoT System`**。
- **後端代碼註解與全庫清理** (`PROJECT/SignalHub/app/Http/Controllers/Api/V9/CallbackAckController.php` 第 12 行等)：
  - 清理「小猴」等非正式詞彙，全面修正為「**遊戲開發商 / 合作系統端**」。
  - 嚴格遵守商務禮儀：面向邱先生（設備夥伴）、侯先生（遊戲系統商），全站排除任何內部調侃簡稱。

### 3. 受眾視角翻轉（全面轉向機台主與業主營運視角）
- **頂部導航列優化** (`PROJECT/SignalHub/resources/views/layouts/app.blade.php`)：
  - **移除右上角 `[REST API]` 按鈕**：消除對機台主無效之工程雜訊。
  - **頁籤業務生活化**：
    - `📡 設定檔` ➔ **`📡 機台管理`**
    - `⚡ 派送記錄` ➔ **`⚡ 開洗分紀錄`**
    - `🔔 Webhooks` ➔ **`🔔 合作推送 (Webhooks)`**
    - `🎛️ 模擬器` ➔ **`🎛️ 機台測試`**
- **硬體黑話人話化**：
  - **模擬器** (`PROJECT/SignalHub/resources/views/signal-hub/simulator.blade.php`)：
    - 頁面標題轉為「機台測試 / 🎛️ 機台信號測試」，說明轉為「模擬現場機台開分與洗分按鍵觸發，即時測試信號推送與回調」。
    - 將「📥 採集輸入腳位 (PCNT 累加里程)」改為 **「📥 實體按鍵模擬 (開分 / 洗分)」**。
    - 將「點擊按鈕 = 現場光耦觸發」改為 **「點擊按鈕 = 模擬現場服務員按下實體鍵」**。
    - 將「📤 控制輸出腳位 (繼電器/控制)」改為 **「📤 繼電器開關輸出 / 電磁閥控制」**。
    - 將「點擊切換高低電位」改為 **「點擊切換輸出開關狀態」**。
  - **腳位設定** (`PROJECT/SignalHub/resources/views/signal-hub/pins.blade.php` 及 guide)：
    - 麵包屑導航同步更新為「📡 機台管理」。
    - 輸出標籤將「繼電器開關 / 控制線路」與「Relay / Open Drain」白話改為 **「繼電器開關輸出 / 電磁閥控制」**。
    - 運作模式說明白話化：
      - 通知型：**「通知型（按一下觸發一次，如洗分）」**。
      - 計數型：**「計數型（連按累加，如開分）」**。

### 4. 【重大業務補齊】開洗分紀錄增加「機台名稱」欄位
- **修改檔案**：
  - `PROJECT/SignalHub/app/Models/SignalWebhookDelivery.php`
  - `PROJECT/SignalHub/app/Http/Controllers/Api/V9/SignalHubController.php`
  - `PROJECT/SignalHub/resources/views/signal-hub/deliveries.blade.php`
- **實作內容**：
  - **後端 Model 與查詢**：
    - `SignalWebhookDelivery` 增加 `$appends = ['machine_name']` 與 `getMachineNameAttribute()`，自動依優先級解析機台自訂名稱（`profile_name`）、設備名稱（`device.name`）、設備晶片號（`device.chip_id`）或事件晶片號（`event.chip_id`）。
    - `SignalHubController::indexDeliveries` Eager Loading 關聯補齊：`profile:id,profile_name,device_id`、`profile.device:id,chip_id,name`、`event:id,chip_id`，確保無 N+1 問題。
    - `SignalHubController::showDelivery` 亦補齊 `profile.device` 關聯。
  - **前端介面展示**：
    - 在「時間」欄位後方正式加入 **「機台」** 欄位（寬度截斷保護、hover 顯示完整名稱）。
    - 點擊「詳情」彈出視窗同步展示「機台名稱」欄位，讓業主有多台機台時能清楚進行對帳與日結查核。

---

## 🚀 部署與遠端驗收記錄

1. **版本控制**：
   - 本機修改完成並通過 `php -l` 語法校驗。
   - 提交 Commit `d73ebd4` 並推送到 GitHub `origin/main`。
2. **遠端 VPS 部署**：
   - 執行 `../../dev_tools/waw_ops.sh deploy sidney` 部署至 `129.153.116.174` (`/www/wwwroot/signal.tg25.win`)。
   - 執行遠端 Artisan 快取清理：`php artisan route:clear && php artisan view:clear`。
3. **實機狀態驗證**：
   - `curl -sI https://signal.tg25.win/login` ➔ **HTTP/2 200**。
   - 驗證登入頁面：密碼顯示/隱藏眼睛按鈕切換邏輯健全，公開規格書連結正常。
   - `curl -sI https://signal.tg25.win/signal-hub/guide` ➔ **HTTP/2 200**（免登入直接直通）。
   - 驗證全站導覽列：右上角 `[REST API]` 已移除，頁籤已更名為「📡 機台管理」、「⚡ 開洗分紀錄」、「🔔 合作推送 (Webhooks)」、「🎛️ 機台測試」。
   - 驗證全站頁腳：已更新為 `WAW Universal Signal Standard (WAW-USS) © 2026 WAW IoT System`。
   - 驗證後端 API：`SignalWebhookDelivery` 關聯載入與 `machine_name` 解析正確（實機測試第一筆回傳機台名稱「實體通訊卡 #01」）。
   - 驗證全庫搜尋：無「老李、老邱、小猴、(Sidney)、REST API」等內部非正式詞彙。
