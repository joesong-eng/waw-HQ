# 任務回報：DB 遷移 廢除 owner_subscriptions

- **任務 ID**：TASK_20261004_INA_DROP_OWNER_SUBSCRIPTIONS
- **執行者**：Ina (Infra / DB)
- **回報時間**：2026-10-04 01:58 CST
- **結論**：⚠️ **暫停執行，回報 HQ 請求澄清**（工單 SQL 與實際 Schema 多處不符，且為破壞性 DDL）

---

## 一、已完成的「先查再做」盤點（鐵律 1）

主機：infra (141.148.165.50)，DB：iotv9，MySQL 8.0.46
連線方式：`sudo mysql --defaults-file=/etc/mysql/debian.cnf`（未使用明文密碼）

### 1.1 owner_subscriptions 現況（實測 2 筆，與工單相符）
| id | owner_id | owner_type | plan_name | started_at | expires_at | status |
|----|----------|------------|-----------|------------|------------|--------|
| 1 | 12 | device_owner | device_service | 2026-09-15 10:14:22 | 2027-12-31 23:59:59 | active |
| 2 | 11 | device_owner | device_service | 2026-09-15 10:14:22 | 2027-12-31 23:59:59 | active |

- users 表查無 id=11 → **owner_id=11 確認為孤兒**（不搬正確）✅
- users id=12 = 家寶科技（role=owner）✅

### 1.2 subscriptions 表實際結構（與工單 SQL 不符）
```
service_type  enum('device','venue') NOT NULL      ← 工單寫 'device_service' ❌ 會報錯
target_id     bigint unsigned NOT NULL             ← 工單寫 NULL ❌ 違反 NOT NULL
tier_code     varchar(50) NULL                     ← 工單寫 'basic'
started_at / expires_at datetime NOT NULL          ← 工單寫 start_date / end_date ❌ 欄位不存在
billing_request_id bigint unsigned NULL
FK: subscriptions.subscriber_id -> users.id
```

### 1.3 【重大】owner_id=12 的資料疑似「早已遷移」
subscriptions 表**已存在** subscriber_id=12 的 2 筆記錄：
| id | subscriber_id | target_id | status | started_at | expires_at |
|----|---------------|-----------|--------|------------|------------|
| 30 | 12 | 43 | active | 2026-09-15 10:14:08 | 2027-12-31 23:59:59 |
| 31 | 12 | 43 | active | 2026-09-15 10:14:22 | 2027-12-31 23:59:59 |

→ subscriptions.id=31 的 started_at/expires_at 與 owner_subscriptions.id=1 **完全一致**（10:14:22）。
→ 若照工單再 INSERT，將產生**重複記錄**（且因欄位錯誤會直接失敗）。

### 1.4 【重大】subscription_audit_logs 歸屬與工單/ADR 描述不符
- 工單與 ADR-003 稱「FK 指向 owner_subscriptions，隨主表一起 drop」。
- **實測：該表無任何 FK**（REFERENTIAL_CONSTRAINTS = 0）。
- 實際欄位為 `subscription_id, event_type, old_status, new_status, remark`（**非** archived migration 的 action/old_value/new_value）。
- 資料實測（2 筆）：
  - id=1: subscription_id=1, event_type=renewed, remark='test'
  - id=2: subscription_id=14, event_type=renewed, remark 內容為 **subscriptions 表**的 JSON 快照（service_type=venue, tier_20, quota_limit=2）
- 代碼實證：`Owner/app/Models/SubscriptionAuditLog.php`（table='subscription_audit_logs'）由
  `Owner/app/Services/SubscriptionService.php:302` 與 `SubscriptionController.php:244` 使用，
  且 SubscriptionService 全程操作的是 **Subscription（subscriptions 表）**，非 OwnerSubscription。
- **結論：subscription_audit_logs 實際是 subscriptions 的稽核表（現行運作中），DROP 會破壞 Owner 後台訂閱稽核功能。** ⛔

### 1.5 代碼端仍大量引用 owner_subscriptions / OwnerSubscription
- **Owner**：CheckSubscriptionExpiry.php、OtaController.php、User.php(hasOne)、NotificationService.php、Events(SubscriptionExpired/Extended/RenewalReminderNeeded)
- **SignalHub**：EnsureSubscriptionActive.php(middleware)、SignalHubController.php:1014、User.php
- 遠端 Owner VPS（129.153.116.174, /www/wwwroot/iot.tg25.win, commit ce76cb3）**仍含上述引用**。
→ 直接 DROP 表將使這些代碼在 runtime 拋錯（需先由 Sophie/Sidney 改代碼，非 Ina 職權）。

---

## 二、工單 SQL 逐條驗證（結論：不可直接執行）

| 工單步驟 | 實際狀況 | 可否執行 |
|----------|----------|----------|
| 2. INSERT ... service_type='device_service', target_id NULL, tier_code='basic', start_date/end_date | 欄位名與值皆錯（enum 無 device_service、target_id NOT NULL、無 start_date 欄位） | ❌ 語法即失敗 |
| 3. 確認新增記錄 | 資料疑似已存在（id=30/31） | ⚠️ 會重複 |
| 4. DROP TABLE subscription_audit_logs | 該表為 subscriptions 現行稽核表，非 owner_subscriptions 子表 | ⛔ 破壞功能 |
| 5. DROP TABLE owner_subscriptions | 代碼仍引用，未先改代碼 | ⛔ 破壞功能 |

---

## 三、建議處置（待 HQ 裁定）

1. **資料遷移**：因 subscriptions 已有 subscriber_id=12 記錄，建議**不重複 INSERT**；請 HQ/Sophie 確認 id=30/31 即為 owner_id=12 的對應訂閱。若確認，此步驟**無需執行**。
2. **subscription_audit_logs**：**不應 DROP**。ADR-003 對其歸屬描述有誤（誤信 archived migration 而非 live schema）。建議保留。
3. **owner_subscriptions DROP**：須**先**由 Sophie（Owner）與 Sidney（SignalHub）完成代碼去引用並部署，經 HQ 核准後，Ina 才執行 DROP。
4. 建議修訂 ADR-003 與本工單，更正上述 Schema 描述。

## 四、待 HQ 決策問題

- Q1：subscriptions.id=30/31 是否即 owner_id=12 的遷移目標？（若是，步驟 2 可省略）
- Q2：subscription_audit_logs 是否確認保留？（Ina 判定：應保留）
- Q3：owner_subscriptions DROP 是否待代碼去引用後再執行？

---

**狀態**：⏸️ 已暫停，未對生產 DB 執行任何 DDL / DML。等待 HQ 指示。

