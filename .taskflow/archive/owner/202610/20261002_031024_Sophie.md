# 任務回報：TASK_20261002_SOPHIE_FIX_M5_WEBHOOK_AND_NOTIFICATION_ALERTS

- **任務 ID**：TASK_20261002_SOPHIE_FIX_M5_WEBHOOK_AND_NOTIFICATION_ALERTS
- **執行者**：Sophie (Owner)
- **完成時間**：2026-10-02
- **狀態**：✅ 完成 (Completed)

---

## 1. 執行項目與修復內容

### 1.1 修復 ProcessWebhookDelivery 類別引用致命 Bug（P0 核心）
- **檔案**：`app/Jobs/ProcessWebhookDelivery.php`
- **問題**：第 208 行 `app(AppServicesNotificationService::class)` 命名空間缺少反斜線，PHP 解析為 `AppServicesNotificationService`（頂層類別），觸發告警時必拋 `Class not found`。
- **修復**：改為 `app(\App\Services\NotificationService::class)`。
- **簽章相容性確認**：`NotificationService::createInboxNotification(int $userId, string $title, string $body, string $type, ?string $actionUrl = null, ?array $actionData = null)`，呼叫端傳 4 個參數完全相容。

### 1.2 Webhook 告警通知內容補強（工單要求：標示 Webhook ID、端點與失敗原因）
- 原本告警僅顯示 delivery ID，資訊不足。
- **過期告警**（`【告警】Webhook 推送已過期`）與**連續失敗告警**（`【告警】Webhook 推送連續失敗`）均補齊：
  - Webhook ID、推送 Delivery ID
  - 端點 URL（`endpoint_url`）
  - 失敗原因（`last_error`，含 cURL / HTTP 錯誤詳情）

### 1.3 檢查設備狀態異動告警協同（DeviceController）
- **檔案**：`app/Http/Controllers/Api/V9/DeviceController.php`（第 1024 行 `in_array($newStatus, ['lost','stolen'])` 區塊）
- **結果**：✅ 現行寫法已正確使用 `app(\App\Services\NotificationService::class)`，無未定義類別或方法，通知類型為 `device_alert`。無需修改。

---

## 2. 部署與版本記錄
- **Git Commits**：
  - `d0000cd` - `fix(m5): 修正 ProcessWebhookDelivery 告警通知類別引用錯誤`
  - `798fbd7` - `feat(m5): Webhook 告警通知內容補齊 Webhook ID、端點與失敗原因`
- **語法檢查**：`php -l app/Jobs/ProcessWebhookDelivery.php` → `No syntax errors detected`
- **全庫掃描**：`grep -rn 'AppServices[A-Z]' app/` → 無任何殘留錯誤命名空間引用
- **遠端部署**：執行 `../../dev_tools/waw_ops.sh deploy owner`，成功部署至 `yd174` (`/www/wwwroot/iot.tg25.win`)，Vite 編譯完成。

---

## 3. 實測驗證佐證（遠端 yd174 真實執行）

### 3.1 Webhook 過期告警鏈（transaction rollback 測試，不污染生產資料）
- 建立測試 webhook（`owner_id=2`，不可達端點），delivery `retry_count=2 / max_retries=3`。
- 觸發 `ProcessWebhookDelivery::handle()` 後：
  - delivery 狀態 → `expired`，retry_count → 3
  - `notification_inbox` 寫入 1 筆 `webhook_alert` 通知：
    ```
    user_id: 2
    title: 【告警】Webhook 推送已過期
    body: Webhook #10 推送 #435 已在重試 3 次後過期，外部系統可能未收到訊號。
          端點：https://mock.fail.example.com/cb。
          失敗原因：cURL error 6: Could not resolve host: mock.fail.example.com。
    ```

### 3.2 Webhook 連續失敗告警鏈
- delivery `retry_count=3 / max_retries=5`（仍可重試但已達告警閾值）。
- 觸發後：
  - delivery 狀態 → `failed`，retry_count → 4，`next_retry_at` 已排程
  - `notification_inbox` 寫入 `webhook_alert` 通知，內容含 Webhook ID、端點與失敗原因，並說明系統將繼續重試。

### 3.3 DeviceController 高危告警（device_alert）
- 以真實設備（#1 娃娃機 #1，owner_id=2）模擬 `lost/stolen` 分支：
  - `createInboxNotification` 成功建立 `device_alert` 通知（ID 28）
  - 無類別/方法錯誤

### 3.4 線上狀態
- `git log`（遠端）：HEAD = `798fbd7`，部署版本正確。
- Queue worker 正常運行（`queue-worker.log` 持續處理 `DeviceUpdated`，無 FAIL）。
- 掃描無殘留 `AppServices*` / `AppModels*` 等錯誤命名空間。

---

## 4. 結論
✅ **完成**。M5 Webhook 告警鏈（連續失敗 + 過期）已全面打通，類別引用致命 Bug 修復，告警內容符合工單要求（含 Webhook ID、端點、失敗原因）；DeviceController 設備狀態異動告警確認正常。生產環境已部署並以真實資料驗證通過。

