# 任務：TASK_20260823_INA_REVIEW_SUBSCRIPTION_MIGRATION

**派發時間**：2026-08-23 16:45  
**優先級**：high  
**負責人**：Ina

---

## 📋 任務內容

### 【重要諮詢與 Migration 預審】WAW 2.0 訂閱與雙所有權架構 Schema 審核

Sophie (Owner) 剛完成 WAW 2.0「訂閱與定價架構重構 (v2.0)」規劃。在正式進入實作與正式執行 Migration 之前，HQ 需要 Ina 先進行資料庫架構審核、相容性確認與潛在矛盾分析。

---

### 一、本次 Schema 變更概要

#### 1. `devices` 表擴充雙所有權欄位
- **背景**：落實採集卡硬件（出資買卡/付月費）與實體遊戲機（分潤分配主體）解耦。
- **預計新增欄位**：
  - `collector_owner_id` (BIGINT UNSIGNED NULL, 採集卡購買人 / 硬件持有者)
  - `machine_owner_id` (BIGINT UNSIGNED NULL, 遊戲機本體所有人 / 分潤對象)
- **舊有欄位**：
  - `owner_id` (現有欄位)：請 Ina 確認現有程式與 DB 中 `owner_id` 的歷史意義與使用情況，後續平滑過渡/回填策略建議。

#### 2. 新建 `subscriptions` 表（取代舊版 owner_subscriptions）
- 欄位規劃：
  - `id` (BIGINT PK)
  - `subscriber_id` (BIGINT FK -> users)
  - `service_type` (ENUM('device', 'venue'))
  - `target_id` (BIGINT - device_id 或 venue_id)
  - `tier_code` (VARCHAR(50) NULL - 僅 venue 服務：tier_20, tier_50, tier_100, tier_200, tier_500)
  - `quota_limit` (INT UNSIGNED DEFAULT 0)
  - `selected_target_ids` (JSON NULL - 方案 Y 自選機台清單)
  - `status` (ENUM('active', 'expired', 'suspended') DEFAULT 'active')
  - `started_at` (DATETIME)
  - `expires_at` (DATETIME)
  - `billing_request_id` (BIGINT NULL)
  - `created_at`, `updated_at`
- 索引：`(subscriber_id, service_type, status)`, `(target_id, service_type)`, `(expires_at, status)`

#### 3. 新建 `billing_cycles` 表（後付款月結帳單明細）
- 欄位規劃：
  - `id` (BIGINT PK)
  - `subscription_id` (BIGINT FK -> subscriptions)
  - `period_start` (DATE)
  - `period_end` (DATE)
  - `days_used` (INT)
  - `days_in_month` (INT)
  - `unit_price` (DECIMAL(10,2))
  - `amount` (DECIMAL(10,2))
  - `status` (ENUM('pending', 'notified', 'paid', 'overdue', 'written_off') DEFAULT 'pending')
  - `grace_ends_at` (DATETIME NULL)
  - `paid_at` (DATETIME NULL)
  - `payment_ref` (VARCHAR(100) NULL)
  - `created_at`, `updated_at`

#### 4. 擴充 `billing_requests` 表
- 新增欄位：`service_type`, `target_ids` (JSON), `target_started_ats` (JSON), `tier_code`, `unit_price`, `quantity`
- 廢棄/移除：`plan_tier`

---

### 二、請 Ina 評估與回報的事項

1. **矛盾與衝突檢查**：
   - 上述新表與欄位設計，與目前生產環境 `iotv9` 資料庫及 `waw_member_production` 是否有任何命名衝突或業務邏輯矛盾？
   - `devices.collector_owner_id` 與 `devices.machine_owner_id` 與現有 `devices.owner_id` 及 `venues.owner_id` 是否有衝突？

2. **既有資料與相容性**：
   - 生產環境目前 `devices` 表共有多少筆資料？`owner_id` 現狀為何？若進行 Migration，如何安全回填（例如預設 `collector_owner_id = owner_id`, `machine_owner_id = owner_id`）？
   - 是否會影響現有 Infra 服務（如 `profit_sharing_service.py`, `kiosk_event_listener.py`, MQTT listener 等）？

3. **Migration 執行策略建議**：
   - 是否有任何欄位型別、索引優化或約束 (Foreign Key / Unique) 建議？
   - 預估 Migration DDL 是否有 Online DDL 鎖表風險？

請 Ina 審查後，輸出詳細評估報告至 outbox。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260823_INA_REVIEW_SUBSCRIPTION_MIGRATION

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Ina

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：Ina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-23 16:45
