# 任務：TASK_20261002_SOPHIE_FIX_M5_WEBHOOK_AND_NOTIFICATION_ALERTS

**派發時間**：2026-10-02
**優先級**：P1 / High（M5 通知系統健全度與 Webhook 告警修復）
**負責人**：Sophie (Owner)
**關聯模組**：Owner (iot.tg25.win / yd174)

---

## 📌 任務背景與目標
依據 2026-09-30 全模組盤點決策，接續 M7 結算管線修復完成後，推進 P1 優先級項目：修復 M5 通知系統與 Webhook 告警機制。
目前 `ProcessWebhookDelivery.php` 存在致命類別引用錯誤（`AppServicesNotificationService`），導致 Webhook 推送重試告警與過期告警觸發時必拋例外。需全面修復並打通 M5 告警通知鏈。

---

## 📋 具體執行項目

### 1. 修復 ProcessWebhookDelivery 類別引用致命 Bug
- **檔案**：`app/Jobs/ProcessWebhookDelivery.php`
- **問題**：第 208 行 `$notificationSvc = app(AppServicesNotificationService::class);` 類別拼寫錯誤且缺少反斜線。
- **改善**：修正為引入或呼叫 `app(\App\Services\NotificationService::class)`，並確認方法參數簽章相容。

### 2. 驗證 Webhook 連續失敗與過期告警通知流
- **檢查邏輯**：
  - `scheduleRetry()` 在 `shouldAlert()` 條件成立時（連續失敗達閾值、過期時）呼叫 `notifyWebhookOwner()`。
  - 確認 `inbox_notifications` 表能正確寫入通知（`type = 'webhook_alert'`，關聯店主 `owner_id`）。
  - 確認通知內容清楚標示 Webhook ID、端點與失敗原因。

### 3. 檢查設備狀態異動告警協同（DeviceController）
- **檔案**：`app/Http/Controllers/Api/V9/DeviceController.php`
- **檢查**：第 1024 行 `in_array($newStatus, ['lost', 'stolen'])` 的告警通知調用是否正常運作，確認無未定義類別或方法。

---

## 🚀 部署與回報標準
1. 確保程式碼通過語法檢查（`php -l`）。
2. Commit 並推送至 `origin/main`。
3. 執行遠端部署（`./dev_tools/waw_ops.sh deploy owner`）。
4. 驗證遠端 `yd174` 部署成功，檢查當日 Laravel Log 無致命錯誤。
5. 完成後依標準格式回報至 `.taskflow/owner/outbox/`。

