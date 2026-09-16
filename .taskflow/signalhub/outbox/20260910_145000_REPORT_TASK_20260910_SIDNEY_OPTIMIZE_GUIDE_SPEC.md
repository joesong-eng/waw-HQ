# 任務回報：TASK_20260910_SIDNEY_OPTIMIZE_GUIDE_SPEC

**完成時間**：2026-09-10 14:50  
**執行者**：sidney (SignalHub)  
**任務依據**：`.taskflow/signalhub/inbox/20260910_141409_TASK_20260910_SIDNEY_OPTIMIZE_GUIDE_SPEC.md`

---

## 執行結果

### 1. 公開免登入存取開放（阻礙排除）
- **修改檔案**：`PROJECT/SignalHub/routes/web.php`
- **實作內容**：
  - 將 `Route::get('signal-hub/guide', ...)` 自 `Route::middleware(['auth'])` 群組移出至公開免登入區（與 `/mock/callback`、`/test-webhook/{token}` 同層）。
  - 保留 `name('signal.guide')` 命名路由，確保內部連結相容性。
  - 外部技術工程師與第三方開發者（如小猴開發者）可直接無障礙查閱規格書，不再觸發 302 導向登入頁。

### 2. 修正重試與定案機制規格（對齊 WAW 法典）
- **修改檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **實作內容**：
  - 第一章系統架構表格與第六章維運審計表格全面移除「3分鐘衝刺重試」描述。
  - 對齊後台 `ProcessWebhookDelivery.php` 與 `SignalWebhookDelivery.php` 之實作，統一規範為「**10 秒極速定案機制（0s, 3s, 6s 重試）**」。
  - 明確標記若 10 秒內經 3 次重試仍未收到有效回應，系統標記為 `expired` 定案並即刻發送 Telegram / Line 系統告警通知。

### 3. 補齊 Webhook Header 安全簽名與防重放規範
- **修改檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **實作內容**：
  - 第三章對接前置作業與第五章 5.1 節新增完整的 HTTP 請求標頭 (Request Headers) 規格卡片：
    - `X-WAW-Signature`：明訂格式為 `sha256={hmac}`（強制帶有 `sha256=` 前綴），是以整個 HTTP Request Raw Body 作為內容進行 HMAC-SHA256 計算之簽名。
    - `X-WAW-Timestamp`：Unix 秒級時間戳（例如 `1725945120`），規範接收端伺服器若判定請求時間與接收端差距超過 300 秒（5 分鐘）應予拒絕作廢，防範中間人重放攻擊 (Replay Attack)。
    - `X-WAW-Delivery`：唯一推送識別號（如 `del_10284`），與 Body 內之 `delivery_id` 一致，做為接收端冪等去重鍵 (Idempotency Key)。
    - `X-WAW-Event`：信號事件類型識別（例如 `signal.counter` 或 `signal.event`）。
    - `User-Agent`：固定為 `WAW-SignalHub/1.0`。

### 4. 補充遊戲商主動離場通知 API (Session End)
- **修改檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **實作內容**：
  - 新增章節「5.4 遊戲商主動通知：玩家離場／分數歸零 (Session End)」。
  - 完整載明呼叫端點 `POST https://signal.tg25.win/api/v9/signal-hub/inbound/session-end`。
  - 詳列 Header 鑑權 `X-WAW-Secret: {your_webhook_secret}` 與請求 JSON Payload 欄位規格（`chip_id`, `machine_number`, `event: "session_end"`, `reason: "points_cleared_to_zero"`, `last_played_duration_seconds`, `occurred_at`）及 HTTP 200 回應範例。

### 5. 快捷導航補充 `/mock/callback` 測試終端
- **修改檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **實作內容**：
  - 於頂部快捷功能工具列中新增高辨識按鈕「🕹️ Mock 對接測試終端」，點擊可另開視窗直接前往 `https://signal.tg25.win/mock/callback`，供工程師進行端點模擬、即時日誌檢視與異步回簽測試。

### 6. 微調 UI2 洗分與串口格式說明
- **修改檔案**：`PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`
- **實作內容**：
  - 5.1 節補充 UI2 洗分特徵說明：洗分動作之 `event_type: "event"` 且 `delta_value: 1`，若機台當前餘額為 0 分，遊戲商回傳 `actual_points: 0` 亦為合法正常回應。
  - 5.3 節地端 USB 串口輸出規格註明單行 JSON 資料結尾均帶有標準換行符 `\n`，現場收銀電腦可使用標準 readline 逐行非阻塞解析。
  - 文件規格版本升級為 `v2.2.0`，認證代號更正為 `SPEC-20260910-V22`。

---

## 驗證紀錄

### 1. Git 版本控制
- **Commit ID**：`eaccbea`
- **Commit 訊息**：`feat(guide): optimize developer guide specification v2.2`
- **分支與推送**：已成功 Push 至 GitHub `origin main`。

### 2. 遠端部署與快取清理
- 執行指令：`../../dev_tools/waw_ops.sh deploy sidney`
- 執行指令：`../../dev_tools/waw_ops.sh remote sidney "cd /www/wwwroot/signal.tg25.win && php artisan route:clear && php artisan view:clear"`
- 結果：Route 與 View compiled cache 均已即時清理完畢。

### 3. 線上真實無 Cookie 存取驗證
```bash
curl -sI https://signal.tg25.win/signal-hub/guide
```
- **HTTP 狀態碼**：`HTTP/2 200`（確認無 302 重定向至 `/login`，外部公開存取已正式生效）。
- **內容驗證**：線上已成功渲染「🕹️ Mock 對接測試終端」、「10 秒極速定案機制」、「X-WAW-Signature (sha256=...)」、「session-end」與「\n 換行符」等完整最新規格。

---

## 結論
✅ 全數完成並已在線部署驗證通過。

---
**回報者**：sidney (SignalHub)  
**回報時間**：2026-09-10 14:50

