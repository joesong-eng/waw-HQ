# WAW 2.0 Core Database Design Specification (Sophie Edition v2)

> **文件版本**: v2.0.0  
> **設計者**: Sophie (wawOwner Agent)  
> **建立日期**: 2026-06-10  
> **目標資料庫**: `waw_core` (iotv9 @ VPS yd174)  
> **狀態**: Draft - Pending HQ Review

---

## 📋 設計摘要

本文件根據 `WAW_2.0_ARCHITECTURE_SPEC.md` 規範，為 `waw_core` 資料庫（wawOwner Laravel 後台）設計 WAW 2.0 第二階段的資料表結構與欄位變更。

### 🎯 設計原則
1. **不重複建表**: 已有 `venues`（場地）、`devices`（機器），不建 `stores`/`machines`
2. **欠款在人不在機**: `outstanding_amount` 加在 `users` 表
3. **外鍵安全**: 使用 `ON DELETE RESTRICT`，禁用 `CASCADE`
4. **跨庫 FK**: 若需引用 `waw_infra` 的表，使用邏輯 FK（應用層維護）
5. **審批與協議分離**: `profit_sharing_proposals` 處理審批流程，`profit_sharing_agreements` 儲存生效協議快照

---

## 🗄️ 現有表分析

### 已存在且不需重建的表
| 現有表名 | WAW 2.0 對應實體 | 說明 |
|---------|-----------------|------|
| `venues` | Store (場地) | 已存在，需補充訂閱相關欄位 |
| `devices` | Machine (機器) | 已存在，需補充訂閱與授權欄位 |
| `profit_sharing_proposals` | 分潤提案 | 已存在，處理審批流程 (pending/approved/rejected) |

### 需要新建的表
| 新表名 | 用途 | 原因 |
|-------|------|------|
| `machine_deployments` | 機台部署歷史 | 記錄機器在不同場地間的搬移軌跡 |
| `profit_sharing_agreements` | 生效協議快照 | 儲存 approved 後的協議內容供分潤計算使用 |
| `machine_transactions` | 交易流水與分帳 | 記錄每筆交易並固化當時的分潤金額 |

---

## 📐 Schema 設計

### 1. ALTER TABLE `users` - 新增欠款欄位

```sql
-- users 表新增累計欠款欄位
ALTER TABLE users
  ADD COLUMN outstanding_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00
  COMMENT '累計欠款（新台幣元），訂閱過期後按日累計，續費/儲值時自動扣除';
```

**設計說明**:
- 欠款是「人」的屬性，不是機器或場地的屬性
- 當場地或機器訂閱過期進入 `arrears` 狀態，系統每日計算並累加至對應 owner 的此欄位
- 下次續費/儲值時，系統強制從支付金額中扣除此欄位金額並歸零

**Laravel Migration 範例**:
```php
public function up()
{
    Schema::table('users', function (Blueprint $table) {
        $table->decimal('outstanding_amount', 12, 2)
              ->default(0.00)
              ->after('email_verified_at')
              ->comment('累計欠款（新台幣元）');
    });
}

public function down()
{
    Schema::table('users', function (Blueprint $table) {
        $table->dropColumn('outstanding_amount');
    });
}
```

---

### 2. ALTER TABLE `venues` - 場地訂閱管理

```sql
-- venues 表新增訂閱狀態與到期日欄位
ALTER TABLE venues
  ADD COLUMN subscription_status ENUM('active', 'arrears', 'suspended') 
    NOT NULL DEFAULT 'active'
    COMMENT '訂閱狀態: active=正常, arrears=欠費運行, suspended=完全中止',
  ADD COLUMN subscription_expires_at DATETIME NULL
    COMMENT '訂閱到期時間，null 表示尚未開通訂閱',
  ADD COLUMN subscription_grace_days INT NOT NULL DEFAULT 7
    COMMENT '寬限期天數（預設 7 天），過期後進入 arrears',
  ADD INDEX idx_subscription_status (subscription_status),
  ADD INDEX idx_subscription_expires_at (subscription_expires_at);
```

**設計說明**:
- `subscription_status`:
  - `active`: 已繳費，功能正常
  - `arrears`: 訂閱過期但允許營運，限制管理功能，累計欠款
  - `suspended`: 惡意欠費超過 30 天後人工切換，切斷通訊
- `subscription_expires_at`: 訂閱到期時間，系統每日檢查並更新狀態
- `subscription_grace_days`: 寬限期配置，允許不同場地有不同寬限天數

**Laravel Migration 範例**:
```php
public function up()
{
    Schema::table('venues', function (Blueprint $table) {
        $table->enum('subscription_status', ['active', 'arrears', 'suspended'])
              ->default('active')
              ->after('address')
              ->comment('訂閱狀態');
        $table->dateTime('subscription_expires_at')
              ->nullable()
              ->after('subscription_status')
              ->comment('訂閱到期時間');
        $table->integer('subscription_grace_days')
              ->default(7)
              ->after('subscription_expires_at')
              ->comment('寬限期天數');
        
        $table->index('subscription_status', 'idx_subscription_status');
        $table->index('subscription_expires_at', 'idx_subscription_expires_at');
    });
}

public function down()
{
    Schema::table('venues', function (Blueprint $table) {
        $table->dropIndex('idx_subscription_status');
        $table->dropIndex('idx_subscription_expires_at');
        $table->dropColumn(['subscription_status', 'subscription_expires_at', 'subscription_grace_days']);
    });
}
```

---

### 3. ALTER TABLE `devices` - 機器訂閱與授權管理

```sql
-- devices 表新增訂閱狀態與授權到期欄位
ALTER TABLE devices
  ADD COLUMN machine_owner_id BIGINT UNSIGNED NULL
    COMMENT '機台主 user_id，null 表示流浪機（未綁定擁有者）',
  ADD COLUMN subscription_status ENUM('active', 'arrears', 'suspended')
    NOT NULL DEFAULT 'active'
    COMMENT '授權狀態: active=已授權, arrears=欠費運行, suspended=完全停機',
  ADD COLUMN subscription_expires_at DATETIME NULL
    COMMENT '授權到期時間，null 表示尚未開通授權',
  ADD COLUMN subscription_grace_days INT NOT NULL DEFAULT 7
    COMMENT '寬限期天數（預設 7 天），過期後進入 arrears',
  ADD CONSTRAINT fk_devices_machine_owner
    FOREIGN KEY (machine_owner_id) REFERENCES users(id)
    ON DELETE RESTRICT,
  ADD INDEX idx_machine_owner_id (machine_owner_id),
  ADD INDEX idx_device_subscription_status (subscription_status),
  ADD INDEX idx_device_subscription_expires_at (subscription_expires_at);
```

**設計說明**:
- `machine_owner_id`: 機台主 ID，允許 null（流浪機託管狀態）
- `subscription_status`: 機器授權狀態，邏輯同 venues
- 外鍵使用 `ON DELETE RESTRICT`，防止誤刪使用者導致機器資料孤立
- 欠費機器依然放行 MQTT 連線與開分，但每日累計欠款至 owner 的 `outstanding_amount`

**Laravel Migration 範例**:
```php
public function up()
{
    Schema::table('devices', function (Blueprint $table) {
        $table->unsignedBigInteger('machine_owner_id')
              ->nullable()
              ->after('id')
              ->comment('機台主 user_id');
        $table->enum('subscription_status', ['active', 'arrears', 'suspended'])
              ->default('active')
              ->after('machine_owner_id')
              ->comment('授權狀態');
        $table->dateTime('subscription_expires_at')
              ->nullable()
              ->after('subscription_status')
              ->comment('授權到期時間');
        $table->integer('subscription_grace_days')
              ->default(7)
              ->after('subscription_expires_at')
              ->comment('寬限期天數');
        
        $table->foreign('machine_owner_id', 'fk_devices_machine_owner')
              ->references('id')->on('users')
              ->onDelete('restrict');
        
        $table->index('machine_owner_id', 'idx_machine_owner_id');
        $table->index('subscription_status', 'idx_device_subscription_status');
        $table->index('subscription_expires_at', 'idx_device_subscription_expires_at');
    });
}

public function down()
{
    Schema::table('devices', function (Blueprint $table) {
        $table->dropForeign('fk_devices_machine_owner');
        $table->dropIndex('idx_machine_owner_id');
        $table->dropIndex('idx_device_subscription_status');
        $table->dropIndex('idx_device_subscription_expires_at');
        $table->dropColumn([
            'machine_owner_id',
            'subscription_status',
            'subscription_expires_at',
            'subscription_grace_days'
        ]);
    });
}
```

---

### 4. CREATE TABLE `machine_deployments` - 機台部署歷史

```sql
CREATE TABLE machine_deployments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  device_id BIGINT UNSIGNED NOT NULL
    COMMENT '機器 ID，對應 devices.id',
  venue_id BIGINT UNSIGNED NOT NULL
    COMMENT '場地 ID，對應 venues.id',
  status ENUM('active', 'inactive') NOT NULL DEFAULT 'active'
    COMMENT '部署狀態: active=當前部署, inactive=已撤機',
  deployed_at DATETIME NOT NULL
    COMMENT '部署/搬入時間',
  removed_at DATETIME NULL
    COMMENT '撤機/搬出時間',
  notes TEXT NULL
    COMMENT '部署備註（搬機原因、特殊說明等）',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_deployments_device
    FOREIGN KEY (device_id) REFERENCES devices(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_deployments_venue
    FOREIGN KEY (venue_id) REFERENCES venues(id)
    ON DELETE RESTRICT,
  
  INDEX idx_device_id (device_id),
  INDEX idx_venue_id (venue_id),
  INDEX idx_status (status),
  INDEX idx_deployed_at (deployed_at),
  INDEX idx_removed_at (removed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='機台部署歷史表，記錄機器在不同場地間的搬移軌跡';
```

**設計說明**:
- 記錄機器在各場地間的完整搬移歷史
- 同一機器同一時間只能有一筆 `status = 'active'` 的記錄（業務邏輯約束）
- 外鍵使用 `RESTRICT` 確保不會因刪除 device/venue 導致歷史資料丟失
- `removed_at` 為 null 時表示當前正在部署

**業務約束（應用層實施）**:
```php
// 部署新機器前，先將該機器的其他 active 記錄設為 inactive
DB::table('machine_deployments')
  ->where('device_id', $deviceId)
  ->where('status', 'active')
  ->update([
    'status' => 'inactive',
    'removed_at' => now()
  ]);

// 再建立新的 active 部署記錄
DB::table('machine_deployments')->insert([
  'device_id' => $deviceId,
  'venue_id' => $venueId,
  'status' => 'active',
  'deployed_at' => now()
]);
```

**Laravel Migration 範例**:
```php
public function up()
{
    Schema::create('machine_deployments', function (Blueprint $table) {
        $table->id();
        $table->unsignedBigInteger('device_id')->comment('機器 ID');
        $table->unsignedBigInteger('venue_id')->comment('場地 ID');
        $table->enum('status', ['active', 'inactive'])
              ->default('active')
              ->comment('部署狀態');
        $table->dateTime('deployed_at')->comment('部署時間');
        $table->dateTime('removed_at')->nullable()->comment('撤機時間');
        $table->text('notes')->nullable()->comment('部署備註');
        $table->timestamps();
        
        $table->foreign('device_id', 'fk_deployments_device')
              ->references('id')->on('devices')
              ->onDelete('restrict');
        $table->foreign('venue_id', 'fk_deployments_venue')
              ->references('id')->on('venues')
              ->onDelete('restrict');
        
        $table->index('device_id', 'idx_device_id');
        $table->index('venue_id', 'idx_venue_id');
        $table->index('status', 'idx_status');
        $table->index('deployed_at', 'idx_deployed_at');
        $table->index('removed_at', 'idx_removed_at');
    });
}

public function down()
{
    Schema::dropIfExists('machine_deployments');
}
```

---

### 5. CREATE TABLE `profit_sharing_agreements` - 生效協議快照

```sql
CREATE TABLE profit_sharing_agreements (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  proposal_id BIGINT UNSIGNED NULL
    COMMENT '來源提案 ID，對應 profit_sharing_proposals.id，null 表示系統預設',
  device_id BIGINT UNSIGNED NOT NULL
    COMMENT '機器 ID，對應 devices.id',
  venue_id BIGINT UNSIGNED NOT NULL
    COMMENT '場地 ID，對應 venues.id',
  machine_owner_id BIGINT UNSIGNED NULL
    COMMENT '機台主 ID，對應 users.id，null 表示流浪機',
  venue_owner_id BIGINT UNSIGNED NOT NULL
    COMMENT '場地主 ID，對應 users.id',
  venue_owner_share DECIMAL(5,2) NOT NULL
    COMMENT '場地主分成比例 (0.00-1.00，例如 0.40 代表 40%)',
  machine_owner_share DECIMAL(5,2) NOT NULL
    COMMENT '機台主分成比例 (0.00-1.00，例如 0.60 代表 60%)',
  system_cut DECIMAL(5,2) NOT NULL DEFAULT 0.00
    COMMENT '平台抽成比例 (0.00-1.00)',
  effective_from DATETIME NOT NULL
    COMMENT '協議生效起始時間',
  effective_to DATETIME NULL
    COMMENT '協議失效時間，null 表示持續有效',
  status ENUM('active', 'expired', 'replaced') NOT NULL DEFAULT 'active'
    COMMENT '協議狀態: active=當前生效, expired=已過期, replaced=被新協議取代',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_agreements_proposal
    FOREIGN KEY (proposal_id) REFERENCES profit_sharing_proposals(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_agreements_device
    FOREIGN KEY (device_id) REFERENCES devices(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_agreements_venue
    FOREIGN KEY (venue_id) REFERENCES venues(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_agreements_machine_owner
    FOREIGN KEY (machine_owner_id) REFERENCES users(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_agreements_venue_owner
    FOREIGN KEY (venue_owner_id) REFERENCES users(id)
    ON DELETE RESTRICT,
  
  INDEX idx_proposal_id (proposal_id),
  INDEX idx_device_venue (device_id, venue_id),
  INDEX idx_effective_from (effective_from),
  INDEX idx_effective_to (effective_to),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='分潤協議生效快照表，儲存 approved 提案的協議內容供分潤計算使用';
```

**設計說明**:
- 當 `profit_sharing_proposals` 中的提案被 approved 後，自動建立此表的記錄
- 此表是「快照」概念，一旦寫入不再修改，確保歷史交易分潤計算的一致性
- `effective_to` 為 null 表示持續有效，直到有新協議取代
- 當建立新協議時，舊協議的 `effective_to` 更新為新協議的 `effective_from`，`status` 改為 `replaced`
- `machine_owner_id` 允許 null，用於處理流浪機的分潤規則（預設機台主 100%，但暫存至託管帳戶）

**與 `profit_sharing_proposals` 的差異**:
| 項目 | profit_sharing_proposals | profit_sharing_agreements |
|------|-------------------------|---------------------------|
| 用途 | 審批流程管理 | 生效協議快照 |
| 狀態 | pending/approved/rejected | active/expired/replaced |
| 可修改 | 審批前可修改 | 一旦建立不可修改 |
| 使用場景 | 後台審批介面 | 交易分潤計算、財務報表 |

**Laravel Migration 範例**:
```php
public function up()
{
    Schema::create('profit_sharing_agreements', function (Blueprint $table) {
        $table->id();
        $table->unsignedBigInteger('proposal_id')->nullable()->comment('來源提案 ID');
        $table->unsignedBigInteger('device_id')->comment('機器 ID');
        $table->unsignedBigInteger('venue_id')->comment('場地 ID');
        $table->unsignedBigInteger('machine_owner_id')->nullable()->comment('機台主 ID');
        $table->unsignedBigInteger('venue_owner_id')->comment('場地主 ID');
        $table->decimal('venue_owner_share', 5, 2)->comment('場地主分成比例');
        $table->decimal('machine_owner_share', 5, 2)->comment('機台主分成比例');
        $table->decimal('system_cut', 5, 2)->default(0.00)->comment('平台抽成比例');
        $table->dateTime('effective_from')->comment('生效起始時間');
        $table->dateTime('effective_to')->nullable()->comment('失效時間');
        $table->enum('status', ['active', 'expired', 'replaced'])
              ->default('active')
              ->comment('協議狀態');
        $table->timestamps();
        
        $table->foreign('proposal_id', 'fk_agreements_proposal')
              ->references('id')->on('profit_sharing_proposals')
              ->onDelete('restrict');
        $table->foreign('device_id', 'fk_agreements_device')
              ->references('id')->on('devices')
              ->onDelete('restrict');
        $table->foreign('venue_id', 'fk_agreements_venue')
              ->references('id')->on('venues')
              ->onDelete('restrict');
        $table->foreign('machine_owner_id', 'fk_agreements_machine_owner')
              ->references('id')->on('users')
              ->onDelete('restrict');
        $table->foreign('venue_owner_id', 'fk_agreements_venue_owner')
              ->references('id')->on('users')
              ->onDelete('restrict');
        
        $table->index('proposal_id', 'idx_proposal_id');
        $table->index(['device_id', 'venue_id'], 'idx_device_venue');
        $table->index('effective_from', 'idx_effective_from');
        $table->index('effective_to', 'idx_effective_to');
        $table->index('status', 'idx_status');
    });
}

public function down()
{
    Schema::dropIfExists('profit_sharing_agreements');
}
```

---

### 6. CREATE TABLE `machine_transactions` - 交易流水與分帳記錄

```sql
CREATE TABLE machine_transactions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  device_id BIGINT UNSIGNED NOT NULL
    COMMENT '機器 ID，對應 devices.id',
  venue_id BIGINT UNSIGNED NOT NULL
    COMMENT '場地 ID，記錄交易發生時的部署場地',
  agreement_id BIGINT UNSIGNED NULL
    COMMENT '協議快照 ID，對應 profit_sharing_agreements.id，null 表示使用預設分成',
  transaction_type VARCHAR(50) NOT NULL
    COMMENT '交易類型: scan_play, coin_insert, cash_exchange 等',
  total_amount DECIMAL(10,2) NOT NULL
    COMMENT '總交易金額（新台幣元）',
  machine_owner_id BIGINT UNSIGNED NULL
    COMMENT '當時的機台主 ID，null 表示流浪機',
  venue_owner_id BIGINT UNSIGNED NOT NULL
    COMMENT '當時的場地主 ID',
  machine_owner_share_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00
    COMMENT '機台主分成實得金額',
  venue_owner_share_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00
    COMMENT '場地主分成實得金額',
  system_cut_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00
    COMMENT '平台抽成金額',
  transaction_time DATETIME NOT NULL
    COMMENT '交易發生時間（實際業務時間）',
  metadata JSON NULL
    COMMENT '交易元數據（MQTT payload、QR code info 等）',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_transactions_device
    FOREIGN KEY (device_id) REFERENCES devices(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_transactions_venue
    FOREIGN KEY (venue_id) REFERENCES venues(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_transactions_agreement
    FOREIGN KEY (agreement_id) REFERENCES profit_sharing_agreements(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_transactions_machine_owner
    FOREIGN KEY (machine_owner_id) REFERENCES users(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_transactions_venue_owner
    FOREIGN KEY (venue_owner_id) REFERENCES users(id)
    ON DELETE RESTRICT,
  
  INDEX idx_device_id (device_id),
  INDEX idx_venue_id (venue_id),
  INDEX idx_transaction_type (transaction_type),
  INDEX idx_transaction_time (transaction_time),
  INDEX idx_machine_owner_id (machine_owner_id),
  INDEX idx_venue_owner_id (venue_owner_id),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='交易流水與分帳記錄表，固化每筆交易的分潤金額與對象';
```

**設計說明**:
- 每筆交易發生時，**固化當時的分成金額與對象**，避免後續修改協議或搬機導致歷史帳目錯亂
- `agreement_id` 記錄使用的協議快照，用於追溯分成規則
- `machine_owner_id` 允許 null，處理流浪機交易（分成暫存至託管帳戶）
- `metadata` 儲存原始 MQTT payload 或 QR code 資訊，供後續審計使用
- 所有金額欄位使用 DECIMAL(10,2) 確保精度

**交易寫入邏輯（應用層實施）**:
```php
// 1. 查詢當前部署關係
$deployment = DB::table('machine_deployments')
    ->where('device_id', $deviceId)
    ->where('status', 'active')
    ->first();

// 2. 查詢生效協議
$agreement = DB::table('profit_sharing_agreements')
    ->where('device_id', $deviceId)
    ->where('venue_id', $deployment->venue_id)
    ->where('status', 'active')
    ->where('effective_from', '<=', now())
    ->where(function($q) {
        $q->whereNull('effective_to')
          ->orWhere('effective_to', '>=', now());
    })
    ->first();

// 3. 若無協議，使用預設分成（機台主 100%）
$machineOwnerShare = $agreement->machine_owner_share ?? 1.00;
$venueOwnerShare = $agreement->venue_owner_share ?? 0.00;
$systemCut = $agreement->system_cut ?? 0.00;

// 4. 計算分成金額
$machineOwnerAmount = $totalAmount * $machineOwnerShare;
$venueOwnerAmount = $totalAmount * $venueOwnerShare;
$systemCutAmount = $totalAmount * $systemCut;

// 5. 寫入交易記錄
DB::table('machine_transactions')->insert([
    'device_id' => $deviceId,
    'venue_id' => $deployment->venue_id,
    'agreement_id' => $agreement->id ?? null,
    'transaction_type' => $transactionType,
    'total_amount' => $totalAmount,
    'machine_owner_id' => $device->machine_owner_id,
    'venue_owner_id' => $venue->owner_id,
    'machine_owner_share_amount' => $machineOwnerAmount,
    'venue_owner_share_amount' => $venueOwnerAmount,
    'system_cut_amount' => $systemCutAmount,
    'transaction_time' => now(),
    'metadata' => json_encode($mqttPayload)
]);
```

**Laravel Migration 範例**:
```php
public function up()
{
    Schema::create('machine_transactions', function (Blueprint $table) {
        $table->id();
        $table->unsignedBigInteger('device_id')->comment('機器 ID');
        $table->unsignedBigInteger('venue_id')->comment('場地 ID');
        $table->unsignedBigInteger('agreement_id')->nullable()->comment('協議快照 ID');
        $table->string('transaction_type', 50)->comment('交易類型');
        $table->decimal('total_amount', 10, 2)->comment('總交易金額');
        $table->unsignedBigInteger('machine_owner_id')->nullable()->comment('機台主 ID');
        $table->unsignedBigInteger('venue_owner_id')->comment('場地主 ID');
        $table->decimal('machine_owner_share_amount', 10, 2)->default(0.00);
        $table->decimal('venue_owner_share_amount', 10, 2)->default(0.00);
        $table->decimal('system_cut_amount', 10, 2)->default(0.00);
        $table->dateTime('transaction_time')->comment('交易發生時間');
        $table->json('metadata')->nullable()->comment('交易元數據');
        $table->timestamps();
        
        $table->foreign('device_id', 'fk_transactions_device')
              ->references('id')->on('devices')->onDelete('restrict');
        $table->foreign('venue_id', 'fk_transactions_venue')
              ->references('id')->on('venues')->onDelete('restrict');
        $table->foreign('agreement_id', 'fk_transactions_agreement')
              ->references('id')->on('profit_sharing_agreements')->onDelete('restrict');
        $table->foreign('machine_owner_id', 'fk_transactions_machine_owner')
              ->references('id')->on('users')->onDelete('restrict');
        $table->foreign('venue_owner_id', 'fk_transactions_venue_owner')
              ->references('id')->on('users')->onDelete('restrict');
        
        $table->index('device_id');
        $table->index('venue_id');
        $table->index('transaction_type');
        $table->index('transaction_time');
        $table->index('machine_owner_id');
        $table->index('venue_owner_id');
        $table->index('created_at');
    });
}

public function down()
{
    Schema::dropIfExists('machine_transactions');
}
```

---

## 🔄 業務流程設計

### 1. 訂閱到期與欠款累計流程

```php
// 每日定時任務：檢查訂閱狀態並累計欠款
// app/Console/Commands/CheckSubscriptionStatus.php

public function handle()
{
    $now = now();
    
    // 1. 檢查場地訂閱
    DB::table('venues')
        ->where('subscription_status', 'active')
        ->where('subscription_expires_at', '<', $now)
        ->update(['subscription_status' => 'arrears']);
    
    // 2. 檢查機器訂閱
    DB::table('devices')
        ->where('subscription_status', 'active')
        ->where('subscription_expires_at', '<', $now)
        ->update(['subscription_status' => 'arrears']);
    
    // 3. 累計場地欠款（月租 1500，按日折算 = 50）
    $arrearsVenues = DB::table('venues')
        ->where('subscription_status', 'arrears')
        ->get();
    
    foreach ($arrearsVenues as $venue) {
        $owner = DB::table('users')->find($venue->owner_id);
        $daysOverdue = $now->diffInDays($venue->subscription_expires_at);
        $dailyRate = 1500 / 30; // 50 元/日
        
        DB::table('users')
            ->where('id', $owner->id)
            ->increment('outstanding_amount', $dailyRate);
    }
    
    // 4. 累計機器欠款（月租 300，按日折算 = 10）
    $arrearsDevices = DB::table('devices')
        ->where('subscription_status', 'arrears')
        ->whereNotNull('machine_owner_id')
        ->get();
    
    foreach ($arrearsDevices as $device) {
        $dailyRate = 300 / 30; // 10 元/日
        
        DB::table('users')
            ->where('id', $device->machine_owner_id)
            ->increment('outstanding_amount', $dailyRate);
    }
    
    // 5. 發送催付通知
    $this->sendArrearNotifications($arrearsVenues, $arrearsDevices);
}
```

### 2. 續費扣除欠款流程

```php
// 續費時自動扣除欠款
// app/Services/SubscriptionService.php

public function renewSubscription($userId, $targetType, $targetId, $months)
{
    $user = User::find($userId);
    $monthlyRate = $targetType === 'venue' ? 1500 : 300;
    $totalAmount = $monthlyRate * $months;
    
    // 1. 先扣除累計欠款
    if ($user->outstanding_amount > 0) {
        $deduction = min($user->outstanding_amount, $totalAmount);
        $user->outstanding_amount -= $deduction;
        $totalAmount -= $deduction;
        
        // 記錄欠款清償
        DB::table('arrears_payments')->insert([
            'user_id' => $userId,
            'amount' => $deduction,
            'paid_at' => now()
        ]);
    }
    
    // 2. 若還有餘額，才用於續費
    if ($totalAmount > 0) {
        $extendMonths = floor($totalAmount / $monthlyRate);
        
        if ($targetType === 'venue') {
            $venue = Venue::find($targetId);
            $venue->subscription_expires_at = $venue->subscription_expires_at 
                ? Carbon::parse($venue->subscription_expires_at)->addMonths($extendMonths)
                : now()->addMonths($extendMonths);
            $venue->subscription_status = 'active';
            $venue->save();
        } else {
            $device = Device::find($targetId);
            $device->subscription_expires_at = $device->subscription_expires_at
                ? Carbon::parse($device->subscription_expires_at)->addMonths($extendMonths)
                : now()->addMonths($extendMonths);
            $device->subscription_status = 'active';
            $device->save();
        }
    }
    
    $user->save();
}
```

### 3. 提案審批後建立協議快照

```php
// 提案審批通過後，自動建立協議快照
// app/Services/ProfitSharingService.php

public function approveProposal($proposalId)
{
    $proposal = ProfitSharingProposal::find($proposalId);
    
    // 1. 更新提案狀態
    $proposal->status = 'approved';
    $proposal->approved_at = now();
    $proposal->save();
    
    // 2. 將舊協議標記為 replaced
    ProfitSharingAgreement::where('device_id', $proposal->device_id)
        ->where('venue_id', $proposal->venue_id)
        ->where('status', 'active')
        ->update([
            'status' => 'replaced',
            'effective_to' => now()
        ]);
    
    // 3. 建立新協議快照
    ProfitSharingAgreement::create([
        'proposal_id' => $proposalId,
        'device_id' => $proposal->device_id,
        'venue_id' => $proposal->venue_id,
        'machine_owner_id' => $proposal->machine_owner_id,
        'venue_owner_id' => $proposal->venue_owner_id,
        'venue_owner_share' => $proposal->venue_owner_share,
        'machine_owner_share' => $proposal->machine_owner_share,
        'system_cut' => $proposal->system_cut ?? 0.00,
        'effective_from' => now(),
        'effective_to' => null,
        'status' => 'active'
    ]);
}
```

---

## 🔐 資料完整性約束

### 外鍵策略
- **所有外鍵使用 `ON DELETE RESTRICT`**，禁用 `CASCADE`
- 原因：財務數據不可因誤刪使用者/場地/機器而連鎖刪除
- 刪除前必須先處理關聯記錄（轉移所有權、封存歷史等）

### 唯一性約束
```sql
-- devices 表的 chip_id 必須唯一
ALTER TABLE devices ADD UNIQUE KEY uk_chip_id (chip_id);

-- 同一機器同一時間只能有一筆 active 部署（業務邏輯約束）
-- 無法用 DB unique constraint 實現，需在應用層檢查
```

### CHECK 約束（MySQL 8.0.16+）
```sql
-- 分成比例總和應為 1.00（允許誤差 0.01）
ALTER TABLE profit_sharing_agreements
  ADD CONSTRAINT chk_share_sum
  CHECK (ABS((venue_owner_share + machine_owner_share + system_cut) - 1.00) < 0.01);

-- 金額不可為負數
ALTER TABLE machine_transactions
  ADD CONSTRAINT chk_positive_amounts
  CHECK (total_amount >= 0 
    AND machine_owner_share_amount >= 0 
    AND venue_owner_share_amount >= 0 
    AND system_cut_amount >= 0);
```

---

## 📊 索引策略

### 查詢場景與對應索引
| 查詢場景 | 涉及表 | 索引 |
|---------|--------|------|
| 查詢機器當前部署位置 | machine_deployments | idx_device_id + idx_status |
| 查詢場地所有機器 | machine_deployments | idx_venue_id + idx_status |
| 查詢生效協議 | profit_sharing_agreements | idx_device_venue + idx_status + idx_effective_from |
| 機台主財務報表 | machine_transactions | idx_machine_owner_id + idx_transaction_time |
| 場地主財務報表 | machine_transactions | idx_venue_owner_id + idx_transaction_time |
| 訂閱到期檢查 | venues/devices | idx_subscription_expires_at + idx_subscription_status |

---

## 🚨 跨庫參照說明

### waw_core 與 waw_infra 的關係
- `waw_core` (iotv9)：wawOwner 後台使用的資料庫
- `waw_infra` (新庫)：waw-infra 微服務使用的資料庫

### 跨庫 FK 處理策略
由於 `waw_core` 與 `waw_infra` 是分離的資料庫，無法使用 DB 層的外鍵約束。若需要引用對方的資料，採用以下策略：

**邏輯外鍵（應用層維護）**:
```php
// 例如：waw_core 的 machine_transactions 需要參照 waw_infra 的 mqtt_events
// 不建立 DB FK，改用邏輯關聯

// 在 Model 中定義關聯
class MachineTransaction extends Model {
    public function getMqttEventAttribute() {
        // 透過 API 或共享 Redis 查詢 waw_infra 的資料
        return app(InfraApiClient::class)->getMqttEvent($this->mqtt_event_id);
    }
}
```

**資料同步策略**:
- 透過 Event-Driven 架構同步關鍵資料
- 使用 Redis Pub/Sub 或 Message Queue 確保資料一致性
- 定期執行資料校驗任務，發現不一致時告警

---

## ⚠️ ALTER TABLE `profit_sharing_proposals` 評估

### 現有表分析
根據 `DB_MANIFEST.md`，現有 `profit_sharing_proposals` 表已處理審批流程：
- 狀態：pending/approved/rejected
- 用途：提案審批管理

### 建議改進方案

**方案 A：在 proposals 加 effective_at 欄位（推薦）**
```sql
ALTER TABLE profit_sharing_proposals
  ADD COLUMN effective_at DATETIME NULL
    COMMENT '協議生效時間，approved 後設定，用於標記何時開始計算分成';
```

優點：
- 無需建立新表 `profit_sharing_agreements`
- 複用現有審批流程
- approved 的提案直接作為生效協議使用

缺點：
- 若提案被修改或刪除，會影響歷史交易的追溯
- 無法保留多版本協議快照

**方案 B：獨立建立 agreements 表（本設計採用）**
- 優點：協議快照不可變，確保歷史資料一致性
- 缺點：需維護兩張表的同步

### HQ 決策點
請 HQ 決定採用方案 A 或方案 B：
- 若營運初期資料量小、協議變更少，可採用方案 A
- 若需嚴格的財務審計與歷史追溯，建議採用方案 B

---

## 📝 Migration 執行順序

```bash
# 1. 修改現有表（users, venues, devices）
php artisan make:migration add_outstanding_amount_to_users_table
php artisan make:migration add_subscription_fields_to_venues_table
php artisan make:migration add_subscription_fields_to_devices_table

# 2. 建立新表（依賴關係由低到高）
php artisan make:migration create_machine_deployments_table
php artisan make:migration create_profit_sharing_agreements_table
php artisan make:migration create_machine_transactions_table

# 3. 執行 Migration
php artisan migrate

# 4. 驗證資料庫結構
php artisan db:show
php artisan tinker --execute="Schema::getColumnListing('users');"
```

---

## 🧪 測試案例

### 1. 訂閱到期與欠款累計測試
```php
// tests/Feature/SubscriptionArrearsTest.php

public function test_venue_subscription_expires_and_accumulates_arrears()
{
    $venue = Venue::factory()->create([
        'subscription_status' => 'active',
        'subscription_expires_at' => now()->subDays(5)
    ]);
    
    Artisan::call('subscription:check-status');
    
    $venue->refresh();
    $owner = $venue->owner;
    
    $this->assertEquals('arrears', $venue->subscription_status);
    $this->assertEquals(250, $owner->outstanding_amount); // 50元/日 * 5天
}
```

### 2. 交易分成固化測試
```php
public function test_transaction_records_profit_sharing_snapshot()
{
    $device = Device::factory()->create();
    $venue = Venue::factory()->create();
    $agreement = ProfitSharingAgreement::factory()->create([
        'device_id' => $device->id,
        'venue_id' => $venue->id,
        'venue_owner_share' => 0.40,
        'machine_owner_share' => 0.60
    ]);
    
    $transaction = MachineTransaction::create([
        'device_id' => $device->id,
        'venue_id' => $venue->id,
        'agreement_id' => $agreement->id,
        'total_amount' => 100.00
    ]);
    
    $this->assertEquals(60.00, $transaction->machine_owner_share_amount);
    $this->assertEquals(40.00, $transaction->venue_owner_share_amount);
    
    // 修改協議後，歷史交易不變
    $agreement->update(['venue_owner_share' => 0.50]);
    $transaction->refresh();
    
    $this->assertEquals(60.00, $transaction->machine_owner_share_amount);
}
```

### 3. 機台搬移歷史測試
```php
public function test_machine_deployment_history_tracks_movements()
{
    $device = Device::factory()->create();
    $venue1 = Venue::factory()->create();
    $venue2 = Venue::factory()->create();
    
    // 初始部署
    $deployment1 = MachineDeployment::create([
        'device_id' => $device->id,
        'venue_id' => $venue1->id,
        'status' => 'active',
        'deployed_at' => now()->subDays(10)
    ]);
    
    // 搬機
    app(DeploymentService::class)->moveDevice($device->id, $venue2->id);
    
    $deployment1->refresh();
    $this->assertEquals('inactive', $deployment1->status);
    $this->assertNotNull($deployment1->removed_at);
    
    $activeDeployment = MachineDeployment::where('device_id', $device->id)
        ->where('status', 'active')
        ->first();
    
    $this->assertEquals($venue2->id, $activeDeployment->venue_id);
}
```

---

## 🔍 後續需與 Ina 協調的項目

由於 Sophie 負責 `waw_core`（wawOwner 後台），Ina 負責 `waw_infra`（基礎設施），以下項目需要跨域協調：

### 1. MQTT 事件與交易記錄的串接
- waw_infra 收到 MQTT 事件後，需通知 waw_core 建立 `machine_transactions` 記錄
- 建議透過 Event Bus 或 HTTP API 實現

### 2. 訂閱狀態的即時同步
- waw_core 的訂閱狀態變更（active/arrears/suspended）需同步至 waw_infra
- waw_infra 的 MQTT Listener 根據狀態決定是否放行連線

### 3. 流浪機託管帳戶設計
- 流浪機產生的分成金額需暫存至「系統託管帳戶」
- 帳戶設計與管理邏輯需雙方共同規劃

---

## 📌 設計限制與已知問題

### 1. 分成比例精度問題
- 使用 DECIMAL(5,2) 儲存分成比例，最多兩位小數
- 若需更高精度（如 0.3333），需調整為 DECIMAL(7,4)

### 2. 同一機器多部署記錄的業務約束
- 資料庫層無法強制「同一機器同一時間只有一筆 active 記錄」
- 需在應用層實施邏輯鎖或事務保護

### 3. 跨庫 FK 的資料一致性
- 邏輯 FK 無法依賴 DB 層的 referential integrity
- 需實施應用層的資料校驗與修復機制

---

## ✅ 驗收標準

設計完成後，需滿足以下標準方可提交 HQ 審核：

- [ ] 所有表結構符合 WAW_2.0_ARCHITECTURE_SPEC.md 規範
- [ ] 外鍵使用 ON DELETE RESTRICT，無 CASCADE
- [ ] outstanding_amount 加在 users 表，不在 devices
- [ ] profit_sharing_proposals 與 agreements 的差異已明確說明
- [ ] 提供完整的 Laravel Migration 程式碼範例
- [ ] 提供業務流程實施邏輯（訂閱到期、續費扣款、協議審批）
- [ ] 提供測試案例涵蓋核心場景
- [ ] 標註需與 Ina 協調的跨域項目
- [ ] 列出設計限制與已知問題

---

## 📮 Sophie 回報

**設計狀態**: ✅ 已完成，等待 HQ 審核  
**執行範圍**: 僅撰寫設計文件，未在任何環境執行  
**需 HQ 決策**:
1. `profit_sharing_agreements` 是否獨立建表（方案 A vs 方案 B）
2. 跨庫 FK 的同步機制由誰負責實施（Sophie vs Ina）
3. 流浪機託管帳戶的設計細節

**後續步驟**:
1. HQ 審核本設計文件
2. 與 Ina 召開技術協調會，確認跨庫串接方案
3. HQ 批准後，Sophie 建立 Laravel Migration 檔案
4. 在 staging 環境執行 Migration 並驗證
5. 通過驗證後部署至 production

---

*文件建立者：Sophie (wawOwner Agent)*  
*建立時間：2026-06-10*  
*文件路徑：/Users/ilawusong/Documents/sysWawIot/HQ/waw2.0_specs/WAW2_CORE_DB_DESIGN_SOPHIE_v2.md*
