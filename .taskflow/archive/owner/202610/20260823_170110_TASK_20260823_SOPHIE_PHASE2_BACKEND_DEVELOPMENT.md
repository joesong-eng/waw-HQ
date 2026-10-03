# 任務：TASK_20260823_SOPHIE_PHASE2_BACKEND_DEVELOPMENT

**派發時間**：2026-08-23 17:01 (Asia/Taipei)  
**優先級**：high  
**負責人**：Sophie (Owner Agent)

---

## 🎯 任務目標：啟動 WAW 2.0 第二階段（後端模型與核心業務服務重構）

Ina 已順利完成生產環境資料庫 Migration 與向下相容處理（`devices` 雙所有權欄位回填 16 筆、新建 `subscriptions` 與 `billing_cycles`、擴充 `billing_requests`）。
現在正式啟動 **Phase 2 後端核心業務服務重構**。

---

## 📋 開發工作清單 (參照 IMPLEMENTATION_ROADMAP_20260823.md)

### 1. 建立 Eloquent Models (T2.1)
- 建立 `app/Models/Subscription.php`：
  - 欄位關聯 (`belongsTo User`, `hasMany BillingCycle`, `casts: selected_target_ids => array`)
  - Scope 輔助方法 (`active()`, `expired()`, `deviceService()`, `venueService()`)
- 建立 `app/Models/BillingCycle.php`：
  - 關聯與狀態判斷 (`isPaid()`, `isOverdue()`)

### 2. 重構 `SubscriptionService` (T2.2)
- 廢除舊版全域單一 `plan_tier` 機制。
- 實作 `getVisibleDeviceIds(int $userId): array`：
  - 取得使用者已訂閱機台 ID 集合（服務費 1,200/台/月）。
  - 加上使用者有效店面訂閱（自選方案 Y 勾選之機台清單 `selected_target_ids`）。
  - 兩者聯集 (Union)，作為業主端可檢視營收與監控之「有效設備集合」。
- 實作 `getVisibleVenueIds(int $userId): array`。
- 實作 `updateVenueQuotaSelection(int $venueId, array $selectedDeviceIds)`：
  - 校驗勾選數量不可超過該店面方案之 `quota_limit`。
  - 儲存至 `subscriptions.selected_target_ids`。

### 3. 重構 `BillingService` (T2.3)
- 實作首月按日折算公式：`(unit_price / days_in_month) * days_used`。
- 實作月中升級換約差額折算：`((new_price - old_price) / days_in_month) * remaining_days`。
- 實作批次多目標帳單建立與 Admin 審核通過後之一對多 `subscriptions` 建立。

### 4. 更新中介軟體 `EnsureSubscriptionActive` (T2.4)
- 改為按請求上下文（`device_id` 或 `venue_id`）動態校驗目標是否包含於當前登入用戶之有效可見集合 (`getVisibleDeviceIds` / `getVisibleVenueIds`)。
- 若未訂閱或已過期，友善導向至訂閱/續費或降級檢視。

---

## 📚 參考規範
- `PROJECT/Owner/_agent/SUBSCRIPTION_SPEC_v2.1.md`
- `PROJECT/Owner/_agent/SUBSCRIPTION_PRICING_SPEC.md`
- `PROJECT/Owner/_agent/IMPLEMENTATION_ROADMAP_20260823.md`
- `PROJECT/Infra/DB_MANIFEST.md`

---

## 📤 回報要求
完成開發與本機測試後，請將成果回報至 `.taskflow/owner/outbox/`。

**派工者**：HQ (System)
