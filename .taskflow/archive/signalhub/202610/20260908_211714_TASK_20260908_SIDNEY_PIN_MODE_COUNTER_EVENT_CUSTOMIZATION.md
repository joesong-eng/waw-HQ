# 任務：TASK_20260908_SIDNEY_PIN_MODE_COUNTER_EVENT_CUSTOMIZATION

**派發時間**：2026-09-08 21:05  
**優先級**：high  
**負責人**：sidney  
**專案**：SignalHub  

---

## 📋 任務背景與目標

現場各機台接線千差萬別，客戶不一定將固定引腳接為開分、洗分或退幣。
為了實現「用戶自定義引腳」的初衷，**韌體端維持忠實採集不變**（所有 UI 輸入腳均回報硬體脈衝計數），而由 **SignalHub 後台提供引腳運作模式切換**：
1. **【🔔 通知型 (Event)】**：適用於洗分按鈕、服務鈴、故障通知等。按下去僅代表「通知小猴/合作端有事件發生」，時間窗口內連按進行去重防抖，不進行數值計數（固定上報單次事件通知，delta: 1）。
2. **【🔢 計數型 (Counter)】**：適用於開分脈衝、退幣馬達數幣、投幣器等。精確記錄每一枚脈衝與累積里程表（raw_value / delta: N），專門用於營業帳務與退幣數額審計。

---

## 🛠️ 具體任務清單

### 1. 介面設定改造：大字清晰、直覺好懂的切換按鈕（優先級：High）
**文件**：`resources/views/signal-hub/pins.blade.php`
- 在輸入腳位 (UI1 ~ UI4) 卡片中，加入醒目、大字、高對比的「模式切換 (Segmented Button)」：
  - **【🔔 通知型】**（標籤：單次事件通知）
    - 說明提示：「像按門鈴，按一次通知一次；連按不重複洗分。適用：洗分按鈕、呼叫鈴」
  - **【🔢 計數型】**（標籤：脈衝精確累加）
    - 說明提示：「像碼錶水錶，有脈衝就累加；每一動都計數。適用：退幣馬達、開分脈衝、投幣器」
- 確保切換狀態一目了然（選中狀態使用主題色高亮邊框與文字）。
- 支援手機/行動裝置好點選的大按鈕版型。
- 預設值：UI1 預設為【計數型】，UI2 預設為【通知型】，UI3/UI4 預設為【計數型】。

### 2. 資料庫與 API 儲存相容（優先級：High）
**文件**：
- `app/Models/SignalPinMapping.php`
- `app/Http/Controllers/Api/V9/SignalHubController.php`
- 確保前端傳遞 `signal_type`（`event` 或 `counter`）能正確被 API 驗證並儲存至 `signal_pin_mappings` 資料表中的 `signal_type` 欄位。

### 3. 事件接收與分流去重邏輯（優先級：High）
**文件**：
- `app/Http/Controllers/Api/V9/SignalHubController.php` 或相關 Event 處理服務
- 當收到採集卡上報、MQTT 轉發或模擬器觸發事件時，根據該腳位的 `signal_type`：
  - **若為 `counter`（計數型）**：維持原累計邏輯，記錄 `raw_value` 與 `delta_value`，派送 Webhook 傳遞數值。
  - **若為 `event`（通知型）**：啟用去重防抖機制（例如 1~2 秒冷卻時間 / Cooldown Window），窗口內連按視為單次事件，Webhook 派發單次事件通知（`delta: 1, signal_type: "event"`），避免合作端接收重複洗分請求。

### 4. 模擬器同步適配（優先級：Medium）
**文件**：`resources/views/signal-hub/simulator.blade.php`
- 模擬器需讀取各引腳之 `signal_type`：
  - 若設定為【通知型】，點擊時作為純事件觸發，不累計脈衝。
  - 若設定為【計數型】，維持防抖窗口內脈衝累加。

### 5. 第三方對接文檔說明（優先級：Low）
**文件**：`docs/THIRD_PARTY_INTEGRATION_GUIDE.md`
- 新增段落說明腳位模式自定義特性（計數型 vs 通知型），以及 Webhook 在這兩種模式下的資料語義差異。

---

## 🚀 驗收與部署標準

1. **代碼與 Git**：
   - 在 `PROJECT/SignalHub` 內完成開發，確認 Git status 乾淨並提交推送。
2. **遠端部署**：
   - 透過 `./dev_tools/waw_ops.sh deploy sidney` 部署至遠端 VPS (`signal.tg25.win`)。
   - 遠端清理快取 (`php artisan optimize:clear`)。
3. **驗證**：
   - 訪問 `https://signal.tg25.win/signal-hub/profiles/{id}/pins` 檢查 UI 切換按鈕與儲存功能。
   - 訪問模擬器確認通知型與計數型之不同行為。
4. **提交回報**：
   - 提交正式報告至 `.taskflow/signalhub/outbox/`。

---

**派發者**：HQ (協調中心)  
**派發時間**：2026-09-08 21:05

