# 任務：TASK_20260910_SIDNEY_OPTIMIZE_GUIDE_SPEC

**派發時間**：2026-09-10 14:30  
**優先級**：high  
**負責人**：sidney (SignalHub)

---

## 📋 任務背景與目標
HQ 已審核你在 `https://signal.tg25.win/signal-hub/guide` 所建置的遊戲商開洗分 API 介面規格說明書。白皮書版面設計與職責劃分非常優秀，為確保外部廠商（如小猴開發者）能順暢對接並符合 WAW 全域標準規範，請依下列審核意見進行修正與補齊。

---

## 🛠️ 具體執行項目

### 1. 開放公開免登入存取（阻礙排除）
- **檔案**：`PROJECT/SignalHub/routes/web.php`
- **說明**：目前 `Route::get('guide', ...)` 位於 `middleware(['auth'])` 內，外部技術人員無帳號點擊會被 302 導向 `/login`。
- **要求**：將 `signal-hub/guide` 路由移至公開免登入區（與 `/mock/callback`、`/test-webhook/{token}` 同層），允許外部直接閱覽。

### 2. 修正重試與定案機制規格（符合 WAW 法典）
- **檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **說明**：第一章與第六章提及「3分鐘衝刺重試」，與 WAW 現行標準衝突。現場店員站在機台前不可能等 3 分鐘。
- **要求**：依據 `SIGNAL_WEBHOOK_AND_SERIAL_STANDARD_v2.md` 與後台 `ProcessWebhookDelivery.php` 之實作，統一修正為「**10 秒極速定案機制（0s, 3s, 6s 重試）**」，超時即判定失敗並發送告警通知。

### 3. 補齊 Webhook Header 安全簽名與防重放規範
- **檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **要求**：在第三章與第五章補充以下 Header 詳細規範（對齊後台代碼）：
  - `X-WAW-Signature`：格式為 `sha256={hmac}`（註明帶有 `sha256=` 前綴），是以整個 HTTP Request Raw Body 作為內容進行 HMAC-SHA256 計算。
  - `X-WAW-Timestamp`：Unix 毫秒/秒時間戳，若請求時間與接收端伺服器差距超過 300 秒（5 分鐘）應予作廢，防範中間人重放攻擊。
  - `X-WAW-Delivery`：唯一推送單號（如 `del_10284`），與 Body 內之 `delivery_id` 一致，做為冪等去重鍵。

### 4. 補充遊戲商主動離場通知 API (Session End)
- **檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **要求**：新增章節或小節，說明當玩家在機台分數歸零（Game Over / 離場）時，遊戲主板主動通知 SignalHub 之規格：
  - 端點：`POST https://signal.tg25.win/api/v9/signal-hub/inbound/session-end`
  - Payload 包含：`chip_id`, `machine_number`, `event: "session_end"`, `reason: "points_cleared_to_zero"`, `last_played_duration_seconds`, `occurred_at`。

### 5. 快捷導航補充 `/mock/callback` 測試終端
- **檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **要求**：在頂部快速功能列中，加入按鈕引導前往你已實作完成的「🕹️ Mock 對接測試終端 (`/mock/callback`)」，使第三方工程師能立即進行連線測試與模擬異步回簽。

### 6. 微調 UI2 洗分與串口格式說明
- **檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **要求**：
  - 5.1 節補充 UI2 洗分時之特徵：`event_type: "event"` 且 `delta_value: 1`，若機台餘額不足，遊戲商回傳 `actual_points: 0` 亦為合法回應。
  - 5.3 節地端 Serial 串口規範註明資料結尾以換行符 `\n` 結尾。

---

## 🚀 驗證與交付流程
1. 本地修改完成後，提交 Git 並 Push 至 origin main。
2. 透過 `./dev_tools/waw_ops.sh deploy sidney` 執行遠端部署。
3. 遠端執行 `php artisan route:clear` 與 `php artisan view:clear`。
4. 使用無 Cookie 的 `curl -sI https://signal.tg25.win/signal-hub/guide` 驗證不再回傳 302，確認回傳 HTTP 200。
5. 按照標準回報格式，提交報告至 `.taskflow/signalhub/outbox/`。

