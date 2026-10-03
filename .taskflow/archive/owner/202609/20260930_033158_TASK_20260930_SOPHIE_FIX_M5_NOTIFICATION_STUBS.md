# 任務工單：TASK_20260930_SOPHIE_FIX_M5_NOTIFICATION_STUBS

**派發時間**：2026-09-30 03:30 (台北時間)  
**優先級**：P1 (通知系統關鍵告警與業務閉環補齊)  
**指派對象**：Sophie (Owner Agent)  
**驗收人**：HQ / Joe

---

## 🎯 任務目標

落實 M5 通知系統中長期殘留的 3 處核心業務與安全告警 Stub，使用既有的 `NotificationService` 串起真實站內信/告警通知：

1. **結算爭議管理員通知** (`SettlementService::sendDisputeNotification`)
2. **設備失竊/遺失高危告警** (`DeviceController::updateStatus`)
3. **Webhook 連續失敗與過期告警** (`ProcessWebhookDelivery::scheduleRetry`)

---

## 📋 具體實作要求

### 一、結算爭議通知補齊 Admin 抄送 (`app/Services/SettlementService.php`)
在 `sendDisputeNotification()` 方法內：
- 除了既有通知爭議相對人之外，補齊 `// TODO: 通知管理員`：
  - 查詢系統內所有 `role === 'admin'` 的使用者。
  - 透過 `$this->notificationService->createInboxNotification()`（或內部對應方法）發送【結算爭議告警】站內信給 Admin，標註結算單號、提出人與金額，導引連結至該結算單詳情。

### 二、設備失竊/遺失高危告警 (`app/Http/Controllers/Api/V9/DeviceController.php`)
在 `updateStatus()` 方法中，當 `in_array($newStatus, ['lost', 'stolen'])` 時：
- 注入/調用 `NotificationService`。
- 發送高危設備告警站內信給該設備所屬的 `device_owner_id` 與場地主：
  - 標題：`【高危告警】設備狀態變更為 ${newStatus}`
  - 內容：包含機台名稱、設備序號/ID、操作時間與警告說明。

### 三、Webhook 失敗告警通知 (`app/Jobs/ProcessWebhookDelivery.php`)
在 `scheduleRetry()` 方法中：
- 當重試次數達到閾值 (`shouldAlert()`) 或已過期 (`markAsExpired()`) 時：
  - 找出該 Webhook/Profile 對應的場地主/擁有者 User。
  - 調用 `NotificationService::createInboxNotification()` 發送 Webhook 傳送失敗告警，避免外部系統斷線而店主毫不知情。

---

## 📦 驗收標準 (Acceptance Criteria)

1. **語法與相依性檢查**：
   - 執行 `php artisan test` 或對應 Unit/Feature Test，無語法或依賴注入錯誤。
   - `NotificationService` 的參數調用與現有 Schema 一致。
2. **Git 與遠端部署**：
   - Commit message 格式：`feat(m5): implement settlement dispute admin notice, device lost alert, and webhook failure notifications`
   - Push 至遠端 main 分支並完成 `waw_ops.sh deploy owner`。
3. **回報格式**：
   - 依據 `SIMPLE_FILE_DISPATCH_PROTOCOL.md` 將回報送達 `.taskflow/owner/outbox/`。
   - 附上遠端部署完成之 git log 與實裝說明。

---
**派發者**：HQ  

