# 回報：TASK_20260823_SOPHIE_PHASE2_BACKEND_DEVELOPMENT

**回報時間**：2026-08-23 18:00 (Asia/Taipei)  
**負責人**：Sophie (Owner Agent)  
**任務編號**：TASK_20260823_SOPHIE_PHASE2_BACKEND_DEVELOPMENT  
**狀態**：✅ 已完成

---

## 📋 任務概述

完成 WAW 2.0 第二階段後端核心業務服務重構，實現雙軌訂閱系統（機台服務 + 店面服務）的底層邏輯與業務規則。

---

## ✅ 完成項目

### T2.1 Eloquent Models ✓

**狀態**：Models 已存在且結構完整，無需重建。

- `app/Models/Subscription.php`
  - 支援 `service_type` (device/venue)
  - 支援 `tier_code` 與 `quota_limit`（店面方案）
  - 支援 `selected_target_ids`（方案 Y 自選機台）
  - 完整的 Scopes 與關聯方法

- `app/Models/BillingCycle.php`
  - 支援月度帳單明細
  - 狀態管理與寬限期判斷
  - 關聯至 Subscription

### T2.2 SubscriptionService 重構 ✓

**位置**：`app/Services/SubscriptionService.php`  
**備份**：`app/Services/SubscriptionService.php.old`

#### 核心方法實作

1. **`getVisibleDeviceIds(int $userId): array`**
   - 取得用戶可見的機台 ID 集合
   - 合併「機台服務訂閱」與「店面服務配額」的聯集
   - 支援方案 Y 自選清單
   - 自動過濾未生效與已過期訂閱

2. **`getVisibleVenueIds(int $userId): array`**
   - 取得用戶可見的店面 ID 集合
   - 僅返回有效的店面服務訂閱

3. **`updateVenueQuotaSelection(int $subscriptionId, array $selectedDeviceIds): void`**
   - 實作方案 Y 自選機台功能
   - 驗證選擇數量不超過配額上限
   - 驗證所選機台確實屬於該店面
   - 記錄審計日誌

4. **`canAccessDevice(int $userId, int $deviceId): bool`**
   - 檢查特定機台是否在用戶可見集合內

5. **`canAccessVenue(int $userId, int $venueId): bool`**
   - 檢查特定店面是否在用戶可見集合內

6. **`getSubscriptionSummary(int $userId): array`**
   - 返回用戶完整訂閱摘要
   - 包含機台服務與店面服務清單
   - 顯示剩餘天數、配額使用情況

7. **`getExpiringSubscriptions(int $daysThreshold): Collection`**
   - 取得即將過期的訂閱（用於提醒通知）

8. **`markExpiredSubscriptions(): int`**
   - 標記過期訂閱（由排程任務調用）
   - 寬限期後自動轉為 expired 狀態

### T2.3 BillingService 重構 ✓

**位置**：`app/Services/BillingService.php`  
**備份**：`app/Services/BillingService.php.old`

#### 核心方法實作

1. **`calculateAmount(...): array`**
   - 支援批次多目標計費
   - 計算公式：`unit_price × quantity × duration_months × (1 - discount_rate)`
   - 返回明細與總金額

2. **`calculateProRatedAmount(float $unitPrice, Carbon $startedAt): float`**
   - 首月按日折算公式
   - `(unit_price / days_in_month) × days_used`

3. **`calculateUpgradeDifference(...): float`**
   - 月中升級換約差額折算
   - `((new_price - old_price) / days_in_month) × remaining_days`

4. **`submitBatchRequest(...): BillingRequest`**
   - 提交批次購買申請
   - 支援多台設備/多個場地一次性購買
   - 支援個別設定 `started_at`（預購功能）

5. **`approveRequest(int $requestId, int $adminId): void`**
   - Admin 核准後自動建立批次訂閱
   - 依 `target_ids` 逐一建立 `Subscription` 記錄
   - 支援欠款扣除邏輯（整合 ProfitSharingService）
   - 使用 DB Transaction 確保原子性

6. **`rejectRequest(...)` / `cancelRequest(...)`**
   - 駁回與撤銷申請功能

7. **`getPricingInfo(): array`**
   - 返回完整定價資訊（機台/店面方案/折扣規則）

### T2.4 EnsureSubscriptionActive 中介軟體更新 ✓

**位置**：`app/Http/Middleware/EnsureSubscriptionActive.php`  
**備份**：`app/Http/Middleware/EnsureSubscriptionActive.php.old`

#### 改動內容

- **廢棄**：舊版全域 `plan_tier` 檢查機制
- **新增**：按請求上下文動態校驗
  - 從 Request 提取 `device_id` 或 `venue_id`
  - 調用 `SubscriptionService::canAccessDevice()` / `canAccessVenue()`
  - 若無權限，返回 403 並提示續費 URL
- **保留**：Admin 繞過檢查
- **保留**：Staff / Sub-agent 使用 `root_id` 訂閱

### T2.5 配置文件更新 ✓

**位置**：`config/subscription.php`  
**備份**：`config/subscription.php.old`

#### 新增配置

```php
'device_unit_price' => 1200.00,  // 機台服務單價

'venue_pricing' => [
    'tier_20'  => ['quota_limit' => 20,  'price' => 2500.00],
    'tier_50'  => ['quota_limit' => 50,  'price' => 5000.00],
    'tier_100' => ['quota_limit' => 100, 'price' => 10000.00],
    'tier_200' => ['quota_limit' => 200, 'price' => 15000.00],
    'tier_500' => ['quota_limit' => 500, 'price' => 25000.00],
],

'discounts' => [
    6  => 0.05,  // 半年繳 5% 折扣
    12 => 0.10,  // 年繳 10% 折扣
],
```

#### 移除配置

- `plans` 陣列（舊版 Pro / Enterprise 固定方案已廢棄）

---

## 🧪 本機測試

由於資料庫 Migration 尚未執行（等待 Ina 完成 Phase 1），本階段僅完成代碼編寫，**尚未進行實際運行測試**。

### 已驗證項目

✅ PHP 語法檢查（無語法錯誤）  
✅ 代碼結構與邏輯審查  
✅ 符合 Laravel 最佳實踐  
✅ 符合規格文檔要求

### 待後續測試項目（Phase 1 完成後）

- SubscriptionService 可見集合查詢正確性
- BillingService 批次建立訂閱流程
- 中介軟體權限檢查邏輯
- 首月折算與升級差額計算準確性

---

## 📁 變更文件清單

### 新增文件
無（Models 已存在）

### 修改文件
- `app/Services/SubscriptionService.php`（完全重寫）
- `app/Services/BillingService.php`（完全重寫）
- `app/Http/Middleware/EnsureSubscriptionActive.php`（完全重寫）
- `config/subscription.php`（重大更新）

### 備份文件
- `app/Services/SubscriptionService.php.old`
- `app/Services/BillingService.php.old`
- `app/Http/Middleware/EnsureSubscriptionActive.php.old`
- `config/subscription.php.old`

---

## 📊 與規格對照

### SUBSCRIPTION_SPEC_v2.1.md ✅
- [x] 雙軌獨立邏輯（機台/店面服務互不影響）
- [x] 可見集合查詢邏輯（聯集去重）
- [x] 方案 Y 自選機台支援
- [x] 預購邏輯（started_at 延後生效）
- [x] 寬限期處理（3 天）

### SUBSCRIPTION_PRICING_SPEC.md ✅
- [x] 機台服務 1,200/台/月
- [x] 店面服務五大級距定價
- [x] 後付款月結模式
- [x] 首月按日折算
- [x] 月中升級差額計算
- [x] 折扣規則（半年 5%、年繳 10%）

### IMPLEMENTATION_ROADMAP_20260823.md ✅
- [x] T2.1 Models 確認
- [x] T2.2 SubscriptionService 重構
- [x] T2.3 BillingService 重構
- [x] T2.4 中介軟體更新

---

## 🔄 後續建議

### Phase 3 開發前置準備

1. **等待 Ina 回報**
   - Phase 1 DB Migration 執行結果
   - 生產環境資料驗證
   - 向下相容測試報告

2. **整合測試準備**
   - 準備測試用戶與測試訂閱資料
   - 設計端到端測試場景
   - 建立 Postman / PHPUnit 測試集

3. **Phase 3 Controller 層開發**
   - RealtimeController::getSummary 改造
   - RevenueController 權限過濾
   - 新增 SubscriptionController API 端點

### 技術債與優化建議

- 考慮為 SubscriptionService 增加快取層（Redis）
- 評估是否需要 Subscription 事件監聽器（自動通知）
- 建議增加 `SubscriptionPolicy` 進行權限細粒度控制

---

## 📝 備註

- 所有舊版文件已備份為 `.old` 後綴，可隨時回滾
- 新版代碼完全遵循 WAW 2.0 規格，與舊版 `OwnerSubscription` 系統**不相容**
- 建議在 Phase 1 完成並驗證後，再進行 Phase 3 開發，避免依賴未就緒的資料表結構

---

**回報者**：Sophie (Owner Agent)  
**回報時間**：2026-08-23 18:00  
**下一步**：等待 Ina 完成 Phase 1 DB Migration 並回報，再啟動 Phase 3 Controller 層開發。

