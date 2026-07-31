# WAW 2.0 基礎設施資料庫設計規格書 v3
# WAW 2.0 Infrastructure Database Design Specification v3

> **文件版本**：v3.0.0  
> **建立日期**：2026-06-10  
> **設計者**：Ina (Infrastructure Agent)  
> **狀態**：Draft / Pending HQ Review  
> **依據文件**：`WAW_2.0_ARCHITECTURE_SPEC.md`

---

## ⚠️ 重要聲明

本文件為 **純設計稿**，尚未在任何環境執行。所有 SQL 語句僅供審查使用。
**禁止直接執行，必須經過 HQ 審核批准後，由 Ina 統一執行 Migration。**

---

## 📋 設計原則

### 1. 最小侵入原則
- 現有表 (`venues`, `devices`, `users`) **只加欄位，不重建**
- 避免破壞現有 1.3M+ 筆 `revenue_facts` 資料
- 保留所有現有外鍵關聯與索引

### 2. 歷史追溯原則
- 新建 `machine_deployments` 記錄機台搬移歷史（`devices.venue_id` 是靜態值無法記歷史）
- 新建 `machine_transactions` 固化交易分成快照（`revenue_facts` 無分成欄位）

### 3. 財務安全原則
- 交易/流水表外鍵禁用 `ON DELETE CASCADE`，改用 `RESTRICT` 或 `SET NULL`
- 欠款記錄在 `users.outstanding_amount`（人的屬性，不是機器屬性）

### 4. 軟性限制原則
- 訂閱過期不中斷 MQTT 通訊與掃碼開分
- 欠費時累計欠款，限制後台管理功能（結帳/提現/報表）
- 高頻 LINE/簡訊催付，避免暴力停機

---

## 🗄️ 現有表結構核查

### 現有核心表（不需重建，僅需加欄位）

#### 1. `venues` (場地/店面)
**現有欄位**：
- `id` (PK), `owner_id` (FK→users), `name`, `address`
- `status` ENUM('active','suspended','closed')
- `default_share_device_owner`, `default_share_venue_owner`
- `created_at`, `updated_at`, `deleted_at`

**需新增欄位**（WAW 2.0 訂閱控制）：
```sql
-- ❌ 尚未執行，僅為設計稿
ALTER TABLE venues 
ADD COLUMN subscription_status ENUM('active','expired','arrears') DEFAULT 'active' 
    COMMENT '訂閱狀態：active=正常, expired=已過期, arrears=欠費運行' 
    AFTER status,
ADD COLUMN subscription_expires_at DATETIME NULL 
    COMMENT '訂閱到期時間' 
    AFTER subscription_status,
ADD INDEX idx_subscription_status (subscription_status),
ADD INDEX idx_subscription_expires_at (subscription_expires_at);
```

---

#### 2. `devices` (機器/採集卡)
**現有欄位**：
- `id` (PK), `chip_id` (UNIQUE), `owner_id` (FK→users), `venue_id` (FK→venues)
- `name`, `type`, `type_id` (FK→device_types)
- `status` ENUM('pending_setup','pending_hardware_deploy','active','maintenance','lost','stolen')
- `share_device_owner`, `share_venue_owner`（分成比例）
- `pulse_to_token`, `out_pulse_to_ticket`
- `created_at`, `updated_at`

**需新增欄位**（WAW 2.0 訂閱控制）：
```sql
-- ❌ 尚未執行，僅為設計稿
ALTER TABLE devices 
ADD COLUMN subscription_status ENUM('active','expired','arrears') DEFAULT 'active' 
    COMMENT '訂閱狀態：active=正常, expired=已過期, arrears=欠費運行' 
    AFTER status,
ADD COLUMN subscription_expires_at DATETIME NULL 
    COMMENT '訂閱到期時間' 
    AFTER subscription_status,
ADD INDEX idx_subscription_status (subscription_status),
ADD INDEX idx_subscription_expires_at (subscription_expires_at);
```

**設計決策**：
- ❌ 不在 `devices` 加 `outstanding_amount`（欠款是人的屬性，不是機器的）
- ✅ `devices.venue_id` 保持靜態值，搬移歷史由 `machine_deployments` 記錄

---

#### 3. `users` (使用者/商戶)
**現有欄位**：
- `id` (PK), `name`, `email`, `phone`, `password`
- `role` ENUM('admin','owner','staff','partner','sub_agent')
- `parent_id`, `upline_id`, `root_id`, `partner_id`（代理層級）
- `commission_rate`, `status`
- `line_id`, `tg_id`（通知綁定）
- `created_at`, `updated_at`

**需新增欄位**（WAW 2.0 欠款累計）：
```sql
-- ❌ 尚未執行，僅為設計稿
ALTER TABLE users 
ADD COLUMN outstanding_amount DECIMAL(12,2) DEFAULT 0.00 
    COMMENT '累計欠款總額（機器+場地訂閱欠費累加）' 
    AFTER commission_rate,
ADD INDEX idx_outstanding_amount (outstanding_amount);
```

**設計決策**：
- 欠款是「人」的屬性，一個商戶可能擁有多台機器/多個場地
- 續費或提現時，系統自動扣除 `outstanding_amount`
- 欠款為 0 時，狀態自動從 `arrears` → `active`

---

## 🆕 新建表結構設計

### 1. `machine_deployments` (機台部署歷史表)

**設計目的**：
- `devices.venue_id` 是靜態值，無法記錄機台搬移歷史
- 財務報表需追溯「某台機器在某個時段部署在哪家店」
- 支援「流浪機」邏輯（`venue_id` 為 NULL 表示未部署）

**表結構**：
```sql
-- ❌ 尚未執行，僅為設計稿
CREATE TABLE machine_deployments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主鍵',
    machine_id BIGINT UNSIGNED NOT NULL COMMENT '關聯 devices.id',
    venue_id BIGINT UNSIGNED NULL COMMENT '關聯 venues.id，NULL=流浪機（未部署）',
    status ENUM('active','inactive') NOT NULL DEFAULT 'active' COMMENT '部署狀態',
    deployed_at DATETIME NOT NULL COMMENT '部署/搬入時間',
    removed_at DATETIME NULL COMMENT '撤機/搬出時間',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (machine_id) REFERENCES devices(id) ON DELETE RESTRICT,
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE RESTRICT,
    
    INDEX idx_machine_status (machine_id, status),
    INDEX idx_venue_status (venue_id, status),
    INDEX idx_deployed_at (deployed_at),
    INDEX idx_removed_at (removed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='機台部署歷史表（記錄機台搬移與場地變更）';
```

**業務約束**：
- 同一 `machine_id` 在同一時間點只能有一筆 `status='active'` 記錄
- 機台搬移時：舊記錄 `status='inactive'`, `removed_at=NOW()`，新記錄 `status='active'`, `deployed_at=NOW()`
- 查詢某時間點機台部署狀態：
  ```sql
  SELECT venue_id FROM machine_deployments 
  WHERE machine_id = ? AND status = 'active' 
    AND deployed_at <= ? AND (removed_at IS NULL OR removed_at > ?)
  LIMIT 1;
  ```

**與現有表的關係**：
- `devices.venue_id` 保持不變，作為「當前部署場地」的快照
- `machine_deployments` 作為歷史追溯表，不影響現有業務邏輯

---

### 2. `machine_transactions` (交易分成固化流水表)

**設計目的**：
- `revenue_facts` 僅記錄原始脈衝與總金額，沒有分成快照
- 後續修改分成比例或搬移機台時，歷史帳目會混亂
- 需在交易發生時**固化分成金額與對象 ID**

**表結構**：
```sql
-- ❌ 尚未執行，僅為設計稿
CREATE TABLE machine_transactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主鍵',
    machine_id BIGINT UNSIGNED NOT NULL COMMENT '關聯 devices.id',
    venue_id BIGINT UNSIGNED NULL COMMENT '交易發生時的部署場地（快照）',
    
    transaction_type VARCHAR(50) NOT NULL COMMENT '交易類型：scan_play, coin_insert, cash_exchange',
    total_amount DECIMAL(12,2) NOT NULL COMMENT '總交易金額（TWD）',
    
    -- 分成固化欄位（交易發生時的快照）
    machine_owner_id BIGINT UNSIGNED NULL COMMENT '機台主 ID（快照，流浪機為 NULL）',
    venue_owner_id BIGINT UNSIGNED NULL COMMENT '場地主 ID（快照，流浪店為 NULL）',
    machine_owner_share_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '機台主分成金額',
    venue_owner_share_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '場地主分成金額',
    system_cut_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '平台抽成金額',
    
    -- 分成比例快照（供對帳驗證）
    machine_owner_share_rate DECIMAL(5,2) NOT NULL COMMENT '機台主分成比例（%）',
    venue_owner_share_rate DECIMAL(5,2) NOT NULL COMMENT '場地主分成比例（%）',
    
    -- 關聯原始事件
    revenue_fact_id BIGINT UNSIGNED NULL COMMENT '關聯 revenue_facts.id（若來自脈衝事件）',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '交易時間',
    
    FOREIGN KEY (machine_id) REFERENCES devices(id) ON DELETE RESTRICT,
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE SET NULL,
    FOREIGN KEY (machine_owner_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (venue_owner_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (revenue_fact_id) REFERENCES revenue_facts(id) ON DELETE SET NULL,
    
    INDEX idx_machine_created (machine_id, created_at),
    INDEX idx_venue_created (venue_id, created_at),
    INDEX idx_machine_owner (machine_owner_id),
    INDEX idx_venue_owner (venue_owner_id),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='交易分成固化流水表（記錄每筆交易的分成快照）';
```

**業務邏輯**：
1. **交易發生時（MQTT 事件或 API 掃碼）**：
   - 查詢 `devices.owner_id` → `machine_owner_id`
   - 查詢當前 `machine_deployments` (status=active) → `venue_id`, `venue_owner_id`
   - 查詢 `profit_sharing_proposals` 或 `devices.share_*` → 分成比例
   - 計算分成金額，寫入 `machine_transactions`

2. **流浪機/流浪店處理**：
   - 若 `devices.owner_id IS NULL` → `machine_owner_id=NULL`, 分成款進入託管帳戶
   - 若 `machine_deployments` 無 active 記錄 → `venue_id=NULL`, `venue_owner_id=NULL`

3. **財務對帳**：
   - 按 `machine_owner_id` 或 `venue_owner_id` 聚合，直接得出各商戶應得金額
   - 不受後續修改分成比例或機台搬移影響

**與 `revenue_facts` 的關係**：
- `revenue_facts` 保持原樣，記錄原始脈衝與總金額
- `machine_transactions` 作為財務結算專用表，記錄分成快照
- 可通過 `revenue_fact_id` 關聯原始事件

---

### 3. `profit_sharing_agreements` (分潤協議表 - 評估中)

**設計考量**：
- 現有 `profit_sharing_proposals` 表已存在（審批流程表）
- 評估是否需要單獨的「協議表」記錄生效後的分成比例
- **待 HQ 決策**：是否在 `profit_sharing_proposals` 加欄位即可？

**暫定設計**（若需新建表）：
```sql
-- ❌ 尚未執行，僅為設計稿，待 HQ 審核決定是否需要
CREATE TABLE profit_sharing_agreements (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主鍵',
    machine_id BIGINT UNSIGNED NOT NULL COMMENT '關聯 devices.id',
    venue_id BIGINT UNSIGNED NOT NULL COMMENT '關聯 venues.id',
    
    machine_owner_share DECIMAL(5,2) NOT NULL COMMENT '機台主分成比例（%）',
    venue_owner_share DECIMAL(5,2) NOT NULL COMMENT '場地主分成比例（%）',
    
    effective_from DATETIME NOT NULL COMMENT '協議生效起算時間',
    effective_to DATETIME NULL COMMENT '協議失效時間（NULL=長期有效）',
    
    proposal_id BIGINT UNSIGNED NULL COMMENT '關聯 profit_sharing_proposals.id（若來自審批流程）',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (machine_id) REFERENCES devices(id) ON DELETE RESTRICT,
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE RESTRICT,
    FOREIGN KEY (proposal_id) REFERENCES profit_sharing_proposals(id) ON DELETE SET NULL,
    
    INDEX idx_machine_effective (machine_id, effective_from, effective_to),
    INDEX idx_venue_effective (venue_id, effective_from, effective_to)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='分潤協議表（記錄機台與場地的分成協議）';
```

**替代方案**：
在 `profit_sharing_proposals` 加欄位：
```sql
-- 替代方案：不建新表，在現有表加欄位
ALTER TABLE profit_sharing_proposals 
ADD COLUMN effective_from DATETIME NULL AFTER approved_at,
ADD COLUMN effective_to DATETIME NULL AFTER effective_from,
ADD INDEX idx_effective (device_id, effective_from, effective_to);
```

**決策點**：
- 若 `profit_sharing_proposals` 主要用於審批流程，建議建新表 `profit_sharing_agreements`
- 若審批通過後直接在 `proposals` 表記錄生效時間，可不建新表
- **請 HQ 決策**

---

## 🔄 資料遷移與初始化策略

### 1. 現有資料初始化

#### A. `venues` 訂閱狀態初始化
```sql
-- ❌ 尚未執行，僅為設計稿
-- 假設所有現有場地預設為 active，到期日設為 1 年後
UPDATE venues 
SET subscription_status = 'active',
    subscription_expires_at = DATE_ADD(NOW(), INTERVAL 1 YEAR)
WHERE subscription_status IS NULL;
```

#### B. `devices` 訂閱狀態初始化
```sql
-- ❌ 尚未執行，僅為設計稿
-- 假設所有現有機器預設為 active，到期日設為 1 年後
UPDATE devices 
SET subscription_status = 'active',
    subscription_expires_at = DATE_ADD(NOW(), INTERVAL 1 YEAR)
WHERE subscription_status IS NULL;
```

#### C. `machine_deployments` 歷史記錄初始化
```sql
-- ❌ 尚未執行，僅為設計稿
-- 將現有 devices.venue_id 轉為初始部署記錄
INSERT INTO machine_deployments (machine_id, venue_id, status, deployed_at, created_at)
SELECT 
    id AS machine_id,
    venue_id,
    'active' AS status,
    COALESCE(created_at, NOW()) AS deployed_at,
    NOW() AS created_at
FROM devices 
WHERE venue_id IS NOT NULL;
```

### 2. 歷史交易資料回填（可選）

**考量點**：
- `revenue_facts` 已有 1.3M+ 筆歷史資料
- 回填至 `machine_transactions` 工作量大，且歷史分成比例可能不準確
- **建議**：僅從 Migration 執行日起記錄新交易，歷史資料保持原樣

**若需回填**（需 HQ 審批）：
```sql
-- ❌ 高風險操作，僅為設計稿，需 HQ 明確批准
INSERT INTO machine_transactions 
(machine_id, venue_id, transaction_type, total_amount, 
 machine_owner_id, venue_owner_id, 
 machine_owner_share_amount, venue_owner_share_amount,
 machine_owner_share_rate, venue_owner_share_rate,
 revenue_fact_id, created_at)
SELECT 
    rf.device_id AS machine_id,
    rf.venue_id,
    'pulse_event' AS transaction_type,
    rf.amount AS total_amount,
    d.owner_id AS machine_owner_id,
    v.owner_id AS venue_owner_id,
    rf.amount * (d.share_device_owner / 100) AS machine_owner_share_amount,
    rf.amount * (d.share_venue_owner / 100) AS venue_owner_share_amount,
    d.share_device_owner AS machine_owner_share_rate,
    d.share_venue_owner AS venue_owner_share_rate,
    rf.id AS revenue_fact_id,
    rf.event_ts AS created_at
FROM revenue_facts rf
JOIN devices d ON rf.device_id = d.id
LEFT JOIN venues v ON rf.venue_id = v.id
WHERE rf.event_ts >= '2026-01-01'  -- 僅回填指定時間段
LIMIT 100000;  -- 分批執行，避免鎖表
```

---

## 🔐 權限與安全設計

### 1. 外鍵約束原則

**財務安全規則**：
- 交易/流水表：`ON DELETE RESTRICT`（禁止級聯刪除）
- 歷史記錄表：`ON DELETE RESTRICT`（禁止級聯刪除）
- 快照欄位：`ON DELETE SET NULL`（保留記錄，ID 設為 NULL）

**範例**：
```sql
-- ✅ 正確：財務表禁止級聯刪除
FOREIGN KEY (machine_id) REFERENCES devices(id) ON DELETE RESTRICT

-- ✅ 正確：快照欄位允許 NULL，不影響歷史記錄
FOREIGN KEY (venue_owner_id) REFERENCES users(id) ON DELETE SET NULL

-- ❌ 錯誤：財務表禁用 CASCADE
FOREIGN KEY (machine_id) REFERENCES devices(id) ON DELETE CASCADE
```

### 2. 索引策略

**查詢場景**：
- 機台主查詢自己的所有機器交易：`idx_machine_owner`
- 場地主查詢自己的場地收入：`idx_venue_owner`
- 時間範圍對帳：`idx_machine_created`, `idx_venue_created`
- 機台搬移歷史查詢：`idx_machine_status`, `idx_deployed_at`

**索引清單**：
```sql
-- machine_deployments
INDEX idx_machine_status (machine_id, status)
INDEX idx_venue_status (venue_id, status)
INDEX idx_deployed_at (deployed_at)
INDEX idx_removed_at (removed_at)

-- machine_transactions
INDEX idx_machine_created (machine_id, created_at)
INDEX idx_venue_created (venue_id, created_at)
INDEX idx_machine_owner (machine_owner_id)
INDEX idx_venue_owner (venue_owner_id)
INDEX idx_transaction_type (transaction_type)
INDEX idx_created_at (created_at)

-- venues (新增)
INDEX idx_subscription_status (subscription_status)
INDEX idx_subscription_expires_at (subscription_expires_at)

-- devices (新增)
INDEX idx_subscription_status (subscription_status)
INDEX idx_subscription_expires_at (subscription_expires_at)

-- users (新增)
INDEX idx_outstanding_amount (outstanding_amount)
```

---

## 📊 業務邏輯實現指引

### 1. 欠費累計與自動扣款

**每日定時任務（Cron Job）**：
```sql
-- ❌ 僅為邏輯示意，實際由後端程式執行
-- 檢查過期但仍在運行的機器，累計欠款
UPDATE users u
JOIN devices d ON u.id = d.owner_id
SET u.outstanding_amount = u.outstanding_amount + (300 / 30)  -- 月租 300，按天折算
WHERE d.subscription_status = 'arrears'
  AND d.subscription_expires_at < NOW();

-- 檢查過期但仍在運行的場地，累計欠款
UPDATE users u
JOIN venues v ON u.id = v.owner_id
SET u.outstanding_amount = u.outstanding_amount + (1500 / 30)  -- 月租 1500，按天折算
WHERE v.subscription_status = 'arrears'
  AND v.subscription_expires_at < NOW();
```

**續費時自動扣除欠款**：
```sql
-- ❌ 僅為邏輯示意，實際由後端程式執行
-- 商戶續費時，優先扣除欠款
START TRANSACTION;

-- 1. 扣除欠款
UPDATE users 
SET outstanding_amount = GREATEST(0, outstanding_amount - :payment_amount)
WHERE id = :user_id;

-- 2. 更新訂閱狀態
UPDATE devices 
SET subscription_status = 'active',
    subscription_expires_at = DATE_ADD(NOW(), INTERVAL 1 MONTH)
WHERE owner_id = :user_id AND id = :device_id;

COMMIT;
```

### 2. 交易分成固化邏輯

**交易發生時（偽代碼）**：
```python
# ❌ 僅為邏輯示意，非實際程式碼
def record_transaction(device_id, total_amount, transaction_type):
    # 1. 查詢機台主
    device = db.query("SELECT owner_id, share_device_owner FROM devices WHERE id = ?", device_id)
    machine_owner_id = device.owner_id
    machine_share_rate = device.share_device_owner
    
    # 2. 查詢當前部署場地
    deployment = db.query(
        "SELECT venue_id FROM machine_deployments WHERE machine_id = ? AND status = 'active'", 
        device_id
    )
    venue_id = deployment.venue_id if deployment else None
    venue_owner_id = None
    venue_share_rate = 0
    
    if venue_id:
        venue = db.query("SELECT owner_id, default_share_venue_owner FROM venues WHERE id = ?", venue_id)
        venue_owner_id = venue.owner_id
        venue_share_rate = venue.default_share_venue_owner
    
    # 3. 計算分成金額
    machine_share_amount = total_amount * (machine_share_rate / 100)
    venue_share_amount = total_amount * (venue_share_rate / 100)
    
    # 4. 寫入交易記錄
    db.execute("""
        INSERT INTO machine_transactions 
        (machine_id, venue_id, transaction_type, total_amount,
         machine_owner_id, venue_owner_id, 
         machine_owner_share_amount, venue_owner_share_amount,
         machine_owner_share_rate, venue_owner_share_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, device_id, venue_id, transaction_type, total_amount,
        machine_owner_id, venue_owner_id,
        machine_share_amount, venue_share_amount,
        machine_share_rate, venue_share_rate)
```

### 3. 機台搬移邏輯

**機台從 A 店搬至 B 店**：
```sql
-- ❌ 僅為邏輯示意，實際由後端程式執行
START TRANSACTION;

-- 1. 關閉舊部署記錄
UPDATE machine_deployments 
SET status = 'inactive',
    removed_at = NOW()
WHERE machine_id = :machine_id AND status = 'active';

-- 2. 建立新部署記錄
INSERT INTO machine_deployments (machine_id, venue_id, status, deployed_at)
VALUES (:machine_id, :new_venue_id, 'active', NOW());

-- 3. 更新 devices.venue_id（保持靜態值同步）
UPDATE devices 
SET venue_id = :new_venue_id
WHERE id = :machine_id;

COMMIT;
```


---

## 🚨 高風險操作清單（需 HQ 明確批准）

以下操作具有高風險，**禁止在未經 HQ 審核的情況下執行**：

### 1. Schema 變更
- ✅ **可執行（經審核後）**：
  - `ALTER TABLE venues ADD COLUMN subscription_status ...`
  - `ALTER TABLE devices ADD COLUMN subscription_status ...`
  - `ALTER TABLE users ADD COLUMN outstanding_amount ...`
  - `CREATE TABLE machine_deployments ...`
  - `CREATE TABLE machine_transactions ...`

- ⚠️ **需 HQ 決策**：
  - `CREATE TABLE profit_sharing_agreements ...` 或在 `profit_sharing_proposals` 加欄位

- ❌ **禁止執行**：
  - 修改現有欄位類型（如 `ALTER COLUMN status ...`）
  - 刪除任何欄位
  - 刪除任何表
  - 修改外鍵約束（除非修正錯誤）

### 2. 資料遷移
- ✅ **可執行（經審核後）**：
  - 初始化訂閱狀態（`UPDATE venues/devices SET subscription_status='active'`）
  - 初始化部署記錄（`INSERT INTO machine_deployments FROM devices`）

- ⚠️ **需 HQ 決策**：
  - 歷史交易回填（`INSERT INTO machine_transactions FROM revenue_facts`）
  - 涉及 1.3M+ 筆資料的批次操作

- ❌ **禁止執行**：
  - 刪除 `revenue_facts` 任何資料
  - 修改現有交易記錄

### 3. 索引與效能
- ✅ **可執行（經審核後）**：
  - 新增索引（提升查詢效能）
  - 分析慢查詢並優化

- ⚠️ **需評估影響**：
  - 刪除現有索引（需確認無業務依賴）

---

## 📝 Migration 執行計畫

### Phase 1: Schema 變更（預估 5 分鐘）
```sql
-- Step 1: venues 加欄位
ALTER TABLE venues 
ADD COLUMN subscription_status ENUM('active','expired','arrears') DEFAULT 'active',
ADD COLUMN subscription_expires_at DATETIME NULL,
ADD INDEX idx_subscription_status (subscription_status),
ADD INDEX idx_subscription_expires_at (subscription_expires_at);

-- Step 2: devices 加欄位
ALTER TABLE devices 
ADD COLUMN subscription_status ENUM('active','expired','arrears') DEFAULT 'active',
ADD COLUMN subscription_expires_at DATETIME NULL,
ADD INDEX idx_subscription_status (subscription_status),
ADD INDEX idx_subscription_expires_at (subscription_expires_at);

-- Step 3: users 加欄位
ALTER TABLE users 
ADD COLUMN outstanding_amount DECIMAL(12,2) DEFAULT 0.00,
ADD INDEX idx_outstanding_amount (outstanding_amount);

-- Step 4: 建立 machine_deployments
CREATE TABLE machine_deployments (...);  -- 完整 SQL 見上文

-- Step 5: 建立 machine_transactions
CREATE TABLE machine_transactions (...);  -- 完整 SQL 見上文
```

### Phase 2: 資料初始化（預估 10 分鐘）
```sql
-- Step 1: 初始化訂閱狀態（假設所有現有實體預設為 active）
UPDATE venues SET subscription_status = 'active', subscription_expires_at = DATE_ADD(NOW(), INTERVAL 1 YEAR);
UPDATE devices SET subscription_status = 'active', subscription_expires_at = DATE_ADD(NOW(), INTERVAL 1 YEAR);

-- Step 2: 初始化部署歷史（將現有 devices.venue_id 轉為 active 部署記錄）
INSERT INTO machine_deployments (machine_id, venue_id, status, deployed_at)
SELECT id, venue_id, 'active', COALESCE(created_at, NOW())
FROM devices WHERE venue_id IS NOT NULL;
```

### Phase 3: 業務邏輯整合（開發任務）
- 修改 MQTT Listener：交易事件寫入 `machine_transactions`
- 修改 API：掃碼開分寫入 `machine_transactions`
- 建立 Cron Job：每日檢查過期訂閱，累計欠款
- 修改後台：欠費時限制結帳/提現/報表功能
- 建立通知任務：每日催付 LINE/簡訊

### Phase 4: 驗證與測試
- 建立測試機器/場地，驗證訂閱狀態切換
- 模擬交易，驗證分成固化邏輯
- 模擬機台搬移，驗證部署歷史記錄
- 模擬欠費，驗證累計與扣款邏輯

---

## 🔍 驗證 SQL

### 1. 檢查訂閱過期實體
```sql
-- 場地過期清單
SELECT id, name, owner_id, subscription_status, subscription_expires_at
FROM venues 
WHERE subscription_expires_at < NOW() AND subscription_status != 'expired';

-- 機器過期清單
SELECT id, chip_id, owner_id, subscription_status, subscription_expires_at
FROM devices 
WHERE subscription_expires_at < NOW() AND subscription_status != 'expired';
```

### 2. 檢查欠款商戶
```sql
-- 欠款商戶清單
SELECT id, name, email, role, outstanding_amount
FROM users 
WHERE outstanding_amount > 0
ORDER BY outstanding_amount DESC;
```

### 3. 檢查機台部署狀態
```sql
-- 流浪機清單（無 active 部署）
SELECT d.id, d.chip_id, d.name, d.owner_id
FROM devices d
LEFT JOIN machine_deployments md ON d.id = md.machine_id AND md.status = 'active'
WHERE md.id IS NULL;

-- 機台搬移歷史
SELECT md.*, v.name AS venue_name, d.chip_id
FROM machine_deployments md
JOIN devices d ON md.machine_id = d.id
LEFT JOIN venues v ON md.venue_id = v.id
WHERE md.machine_id = :device_id
ORDER BY md.deployed_at DESC;
```

### 4. 檢查分成固化記錄
```sql
-- 機台主收入對帳
SELECT 
    machine_owner_id,
    u.name AS owner_name,
    COUNT(*) AS transaction_count,
    SUM(machine_owner_share_amount) AS total_income
FROM machine_transactions mt
JOIN users u ON mt.machine_owner_id = u.id
WHERE mt.created_at >= '2026-01-01'
GROUP BY machine_owner_id, u.name
ORDER BY total_income DESC;

-- 場地主收入對帳
SELECT 
    venue_owner_id,
    u.name AS owner_name,
    COUNT(*) AS transaction_count,
    SUM(venue_owner_share_amount) AS total_income
FROM machine_transactions mt
JOIN users u ON mt.venue_owner_id = u.id
WHERE mt.created_at >= '2026-01-01'
GROUP BY venue_owner_id, u.name
ORDER BY total_income DESC;
```

---

## 📚 參考文件

### 上游依據
- `/Users/ilawusong/Documents/sysWawIot/HQ/waw2.0_specs/WAW_2.0_ARCHITECTURE_SPEC.md`
  - 核心業務規則與實體拆分邏輯
  - 訂閱控制與軟性限制機制

### 現有資料庫
- `/Users/ilawusong/Documents/sysWawIot/tg25-infra/_agent/DB_MANIFEST.md`
  - 現有表結構清單
  - 避免重複建表

### 部署規範
- `/Users/ilawusong/Documents/sysWawIot/tg25-infra/GEMINI.md`
  - VPS 部署流程與坑手冊
  - DB 連線資訊

---

## ✅ 設計完整性檢查清單

### Schema 設計
- [x] 現有表僅加欄位，不重建
- [x] 新表符合業務需求（部署歷史、交易固化）
- [x] 外鍵約束符合財務安全原則（RESTRICT/SET NULL）
- [x] 索引覆蓋主要查詢場景
- [x] 欄位類型與長度合理
- [x] 註釋完整清晰

### 業務邏輯
- [x] 訂閱狀態定義明確（active/expired/arrears）
- [x] 欠費累計邏輯可行
- [x] 交易分成固化邏輯完整
- [x] 機台搬移歷史追溯可行
- [x] 流浪機/流浪店處理邏輯明確

### 資料遷移
- [x] 初始化策略明確
- [x] 歷史資料處理方案清晰
- [x] 高風險操作已標註

### 驗證與測試
- [x] 提供驗證 SQL
- [x] 明確測試場景
- [x] 回滾方案（保留原表結構）

---

## 🚀 後續待辦（HQ 審核後）

### 設計確認
- [ ] HQ 審核 Schema 設計
- [ ] HQ 決策是否需要 `profit_sharing_agreements` 表
- [ ] HQ 決策是否回填歷史交易資料

### 實施準備
- [ ] 建立 Migration 腳本（依審核結果）
- [ ] 建立回滾腳本
- [ ] 準備測試資料
- [ ] 建立驗證腳本

### 業務整合
- [ ] MQTT Listener 整合 `machine_transactions`
- [ ] API 整合 `machine_transactions`
- [ ] Cron Job 欠款累計任務
- [ ] 後台限制功能開發
- [ ] LINE/簡訊催付任務

### 部署與驗證
- [ ] 在測試環境執行 Migration
- [ ] 驗證業務邏輯
- [ ] 效能測試
- [ ] 生產環境部署

---

## 📞 聯繫與回報

**設計者**：Ina (Infrastructure Agent)  
**審核者**：HQ (Hera)  
**文件狀態**：Draft / Pending Review  
**建立時間**：2026-06-10  

**回報方式**：
```bash
bash ../HQ/scripts/agent_report_to_hq_v2.sh ina "WAW2_INFRA_DB_DESIGN_INA_v3.md 已完成，等待審核" ../HQ
```

---

**⚠️ 再次聲明**：本文件所有 SQL 語句均為設計稿，尚未在任何環境執行。  
**禁止直接執行，必須經過 HQ 審核批准後，由 Ina 統一執行 Migration。**

---

*文件結束*
