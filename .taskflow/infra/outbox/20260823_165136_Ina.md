# 任務回報：TASK_20260823_INA_REVIEW_SUBSCRIPTION_MIGRATION

**完成時間**：2026-08-23 17:30
**執行者**：Ina

---

## 執行結果

### 一、生產環境現況調查結果

#### 1. `devices` 表現況
- **生產筆數**：共 **16 筆** 裝置，全部 `owner_id` 均非 NULL（16/16）
- **`owner_id` 目前語義**：查閱 `profit_sharing_service.py` 確認，現有 `devices.owner_id` 對應「**硬件持有者**（採集卡出資人）」，同時也是「分潤接收人（machine_owner_id）」— 也就是說，目前系統中採集卡所有人 = 遊戲機分潤人，兩者尚未解耦。
- **目前資料分布**：user_id=2 持有 13 台、user_id=1 持有 2 台測試機、user_id=5 持有 1 台（長義娛樂）
- **現有索引**：`devices_owner_id_status_index(owner_id, status)`、`devices_owner_id_index(owner_id)` 均存在

#### 2. `owner_subscriptions` 現況
- **現有欄位**：id, owner_id, owner_type (enum: device_owner/venue_owner), plan_name, started_at, expires_at, status (active/expired/cancelled), created_at, updated_at
- **資料筆數**：**0 筆**（尚未有正式訂閱記錄）
- 現行訂閱狀態是透過 `devices.subscription_status` 和 `venues.subscription_status` 欄位直接記錄

#### 3. `billing_requests` 現況
- **現有欄位**：id, owner_id, amount, period_start, period_end, status (pending/paid/failed/cancelled), paid_at, created_at, updated_at
- **資料筆數**：**0 筆**（空表）
- **待廢棄欄位確認**：`plan_tier` — 現有結構中**不存在** `plan_tier` 欄位，Sophie 規格書說「廢棄/移除 plan_tier」可能是指舊版設計草稿殘留，**無需執行移除**

#### 4. `venues` 表
- 含有 `owner_id`（場館所有人）、`subscription_status`、`subscription_expires_at`、`outstanding_amount` 等欄位

---

### 二、矛盾與衝突評估

#### ✅ 命名層面：無直接衝突
新增 `devices.collector_owner_id` 與 `devices.machine_owner_id` 為**全新欄位**，與現有 `devices.owner_id` 及 `venues.owner_id` 名稱不衝突。

#### ⚠️ 語義層面：須明確說明轉換規則
| 欄位 | 舊語義 | 新語義 | 轉換建議 |
|------|--------|--------|----------|
| `devices.owner_id` | 採集卡出資人 = 分潤人（二合一） | 保留作向後相容欄位，或正式標記為「採集卡所有人」別名 | **不建議刪除**，建議保留並設為 `collector_owner_id` 的同義欄位 |
| `devices.collector_owner_id` | （新增）採集卡/硬件持有者 | 硬件出資人 | 回填：`collector_owner_id = owner_id` |
| `devices.machine_owner_id` | （新增）遊戲機本體所有人/分潤對象 | 分潤接收人 | 初始回填：`machine_owner_id = owner_id` |

> ⚠️ **重要警告**：`profit_sharing_service.py` 第 43-44 行直接用 `d.owner_id as machine_owner_id` 查詢作為分潤接收人。Migration 後若業務上 `machine_owner_id` 與 `owner_id` 出現分歧，**必須同步更新此查詢**，否則分潤計算會持續使用舊欄位導致錯誤。

#### ⚠️ `subscriptions` 表：命名與 `owner_subscriptions` 共存問題
新建 `subscriptions` 表同時存在舊版 `owner_subscriptions` 表，兩者並存容易造成混淆。建議：
- Migration 完成後，將 `owner_subscriptions` 標記廢棄並最終 DROP
- 兩表並存期間，所有新業務邏輯一律寫入 `subscriptions`

#### ✅ `billing_cycles` 表：無命名衝突
iotv9 中目前無同名表，可直接新建。

#### ⚠️ `subscriptions.target_id` 多態設計風險
`target_id` 欄位同時指向 `devices.id` 或 `venues.id`（由 `service_type` 區分），屬於「多態關聯」設計。無法加 Foreign Key 約束，資料完整性需由應用層保證。建議：
- 新增 CHECK constraint 或 Application-level validation
- 考慮改為 `device_id BIGINT NULL` + `venue_id BIGINT NULL`（互斥），可加 FK 且更清晰

---

### 三、現有服務影響評估

| 服務 | 影響欄位 | 影響程度 | 說明 |
|------|---------|---------|------|
| `profit_sharing_service.py` | `devices.owner_id` (作為 machine_owner_id) | **🔴 高** | 新 schema 生效後須改為讀取 `machine_owner_id` |
| `kiosk_event_listener.py` | `devices` (只查 chip_id, node_id) | ✅ 無影響 | 不涉及 owner 欄位 |
| `daily_arrears_accumulation.py` | `devices.owner_id`, `devices.subscription_status` | ⚠️ 中 | 累計欠費以 `owner_id` 為準，若雙所有權後需分別對採集卡主/遊戲機主收費，邏輯需重構 |
| MQTT Listener | `devices` 表（查詢 chip_id/status） | ✅ 無影響 | 不涉及 owner 相關欄位 |
| `billing_requests`（現有結構） | 擴充新欄位 | ⚠️ 中 | 現有 0 筆資料，擴充安全；但需更新讀取此表的所有程式 |

---

### 四、Migration DDL 策略建議

#### 4.1 `devices` 表擴充（ADD COLUMN）
```sql
-- Online DDL，僅 ADD COLUMN，無需重建全表（InnoDB 支援 INSTANT DDL）
ALTER TABLE devices
  ADD COLUMN collector_owner_id BIGINT UNSIGNED NULL AFTER owner_id,
  ADD COLUMN machine_owner_id   BIGINT UNSIGNED NULL AFTER collector_owner_id,
  ADD INDEX idx_devices_collector_owner (collector_owner_id),
  ADD INDEX idx_devices_machine_owner   (machine_owner_id);
```

**鎖表風險**：MySQL 8.0 支援 INSTANT ADD COLUMN，**無鎖表風險**。需確認 infra 的 MySQL 版本。

#### 4.2 資料回填（16筆，極低風險）
```sql
-- 安全回填：初始均等同於現有 owner_id
UPDATE devices
SET collector_owner_id = owner_id,
    machine_owner_id   = owner_id
WHERE collector_owner_id IS NULL;
```

#### 4.3 新建 `subscriptions` 表
```sql
CREATE TABLE subscriptions (
  id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  subscriber_id  BIGINT UNSIGNED NOT NULL,
  service_type   ENUM('device','venue') NOT NULL,
  target_id      BIGINT UNSIGNED NOT NULL,
  tier_code      VARCHAR(50) NULL,
  quota_limit    INT UNSIGNED NOT NULL DEFAULT 0,
  selected_target_ids JSON NULL,
  status         ENUM('active','expired','suspended') NOT NULL DEFAULT 'active',
  started_at     DATETIME NOT NULL,
  expires_at     DATETIME NOT NULL,
  billing_request_id BIGINT UNSIGNED NULL,
  created_at     TIMESTAMP NULL,
  updated_at     TIMESTAMP NULL,
  INDEX idx_sub_subscriber_type_status (subscriber_id, service_type, status),
  INDEX idx_sub_target                 (target_id, service_type),
  INDEX idx_sub_expires_status         (expires_at, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**建議補充**：`FOREIGN KEY (subscriber_id) REFERENCES users(id)`（users 表存在，可加）

#### 4.4 新建 `billing_cycles` 表
```sql
CREATE TABLE billing_cycles (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  subscription_id BIGINT UNSIGNED NOT NULL,
  period_start    DATE NOT NULL,
  period_end      DATE NOT NULL,
  days_used       INT NOT NULL,
  days_in_month   INT NOT NULL,
  unit_price      DECIMAL(10,2) NOT NULL,
  amount          DECIMAL(10,2) NOT NULL,
  status          ENUM('pending','notified','paid','overdue','written_off') NOT NULL DEFAULT 'pending',
  grace_ends_at   DATETIME NULL,
  paid_at         DATETIME NULL,
  payment_ref     VARCHAR(100) NULL,
  created_at      TIMESTAMP NULL,
  updated_at      TIMESTAMP NULL,
  FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
  INDEX idx_bc_subscription (subscription_id),
  INDEX idx_bc_status_grace (status, grace_ends_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 4.5 `billing_requests` 擴充
```sql
ALTER TABLE billing_requests
  ADD COLUMN service_type      ENUM('device','venue') NULL AFTER owner_id,
  ADD COLUMN target_ids        JSON NULL,
  ADD COLUMN target_started_ats JSON NULL,
  ADD COLUMN tier_code         VARCHAR(50) NULL,
  ADD COLUMN unit_price        DECIMAL(10,2) NULL,
  ADD COLUMN quantity          INT UNSIGNED NULL;
-- 注意：現有 plan_tier 欄位不存在，無需 DROP
```

---

### 五、整體風險評估

| 風險項目 | 等級 | 說明 |
|---------|------|------|
| 鎖表風險 | ✅ 低 | 全部 ADD COLUMN，MySQL 8.0 支援 INSTANT，16筆小表 |
| 資料遺失風險 | ✅ 低 | owner_subscriptions 和 billing_requests 均為 0 筆 |
| 程式相容性風險 | 🔴 高 | profit_sharing_service.py 必須同步更新 |
| 語義混淆風險 | ⚠️ 中 | owner_id / collector_owner_id / machine_owner_id 並存，需更新所有相關文件 |

---

## 結論

✅ **Schema 設計整體可行，建議 migration 前完成以下事項：**

1. **必須先修改** `profit_sharing_service.py`：將 `d.owner_id as machine_owner_id` 改為讀取新的 `d.machine_owner_id` 欄位（或透過應用層 fallback 邏輯過渡）
2. **`billing_requests.plan_tier`** 不存在於現有 DB，無需 DROP 操作
3. **`subscriptions.target_id` 多態設計**建議 HQ 與 Sophie 再確認是否接受 FK 缺失風險，或改為雙欄位設計
4. **Migration 執行建議**：依序執行 devices 擴充 → 資料回填 → 建 subscriptions → 建 billing_cycles → 擴充 billing_requests
5. **並存期間**：保留 `owner_subscriptions` 表（0筆），遷移完成後再 DROP

---
**回報者**：Ina
**回報時間**：2026-08-23 17:30

