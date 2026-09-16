# WAW 2.0 Phase 2 架構評估報告

**任務**：TASK_20260916_INA_WAW2_PHASE2_DB_EVALUATION
**完成時間**：2026-09-16 21:30
**執行者**：Ina (Infra Master)
**性質**：純評估，零線上異動

---

## 一、現況資料鏈盤點與衝擊分析

### 1.1 iotv9.devices 現行依賴清單

| 服務 | 讀寫方式 | 主要欄位 |
|------|---------|---------|
| **listener.py** (MQTT) | 雙寫 devices + machines | last_seen_at、chip_id、firmware_ver、owner_id（INSERT IGNORE 新設備） |
| **credit-relay FastAPI** | 讀 devices | pulse_to_token（開分計算）、chip_id（查設備）、public_token（by-token 端點）、config_json |
| **device_status_service** | 讀 devices | last_seen_at（降級 fallback，優先查 machines 再 devices） |
| **profit_sharing_service** | 讀 devices | venue_id、COALESCE(machine_owner_id, owner_id)、collector_owner_id、pulse_to_token |
| **Owner (Laravel)** | 讀寫 devices | owner_id、status（arrears 攔截）、subscription_status、venue_id |
| **SignalHub (Laravel)** | 讀 devices（跨庫） | id、owner_id（建立 signal_profile 授權驗證）、device_assignments 快照 |
| **Alliance 跨庫同步** | 寫 iotv9.devices | 9/14 上線，出貨時同步 chip_id、status、owner 等欄位 |
| **Member (Laravel)** | 透過 Infra API | 間接透過 by-token / by-node 端點 |

### 1.2 生產環境重要發現：machines 三表已存在於 iotv9

警告：TODO.md 描述「需要設計 machines 等 4 張新表」，但生產庫 iotv9 內已實際存在以下表：

| 表名 | 狀態 |
|------|------|
| iotv9.machines | 已建，listener.py 已雙寫 |
| iotv9.machine_deployments | 已建 |
| iotv9.machine_transactions | 已建，profit_sharing_service 寫入 |

結論：Phase 2 的「waw_infra 新庫 4 張表」中，有 3 張已在 iotv9 落地。評估重心應轉為「如何安全地物理分庫」，而非重新設計建表。

---

## 二、現有 Schema 審查

### 2.1 iotv9.devices（現行主表）

    chip_id VARCHAR(50) UNIQUE NOT NULL
    public_token VARCHAR(64) UNIQUE NULL        <- 9/13 已加
    owner_id / collector_owner_id / machine_owner_id BIGINT NULL
    venue_id BIGINT NULL
    pulse_to_token DECIMAL(10,2) DEFAULT 1.00
    subscription_status ENUM('active','expired','arrears') DEFAULT 'expired'
    status ENUM('pending_setup','active','maintenance','lost')
    machine_number VARCHAR(64) NULL             <- 9/03 已加
    machine_name VARCHAR(128) NULL              <- 9/03 已加

### 2.2 iotv9.machines（WAW 2.0 新表）

    chip_id VARCHAR(50) UNIQUE NOT NULL
    machine_owner_id BIGINT NULL               <- 無 collector_owner_id（雙產權不完整）
    pulse_to_token DECIMAL(10,2) DEFAULT 0.00
    subscription_status ENUM('active','arrears','suspended')
    status ENUM('pending_setup','active','maintenance','lost','stolen')
    lifetime_pulse_in / lifetime_pulse_out BIGINT <- devices 缺少此兩欄

欄位差異（devices vs machines）：

| 欄位 | devices | machines |
|------|---------|---------|
| collector_owner_id | 有 | 缺 |
| venue_id | 有 | 缺 |
| public_token | 有 | 缺 |
| machine_number / machine_name | 有 | 缺 |
| placement_type | 缺 | 有 |
| share_device_owner / share_venue_owner | 缺 | 有 |
| lifetime_pulse_in / lifetime_pulse_out | 缺 | 有 |

### 2.3 machine_deployments

    machine_id BIGINT -> machines.id
    venue_id BIGINT
    store_id BIGINT NULL
    status ENUM('active','inactive')
    deployed_at / removed_at

問題：machine_id 關聯 machines，但 machines 缺 venue_id — 部署歷史已分離，主表地理資訊未同步。

### 2.4 machine_transactions

    machine_id BIGINT
    venue_id BIGINT
    store_owner_id / machine_owner_id BIGINT NULL
    transaction_type ENUM('top_up','withdrawal','division','refund')
    store_owner_share_amount / machine_owner_share_amount / system_cut_amount DECIMAL(12,2)

profit_sharing_service.py 目前寫入此表。

---

## 三、跨庫同步衝擊分析

### 3.1 Alliance -> iotv9.devices 同步機制

遠端 SHOW TRIGGERS FROM alliance_db 回空（DB 使用者無 TRIGGER 查看權限），需 Allie 確認實際機制（HTTP API 橋接或直接跨庫寫入）。

若未來目標表從 devices 改為 machines 的衝擊：
- HTTP 橋接方式：改動限於 Infra API，Alliance 無需改程式碼 -> 低風險
- 直接跨庫 SQL：Alliance 程式碼需同步更新目標表名 -> 中風險，需協調 Allie
- machines 表目前缺 venue_id、public_token、machine_number，出貨同步欄位需補齊

### 3.2 SignalHub device_assignments 衝擊

SignalHub device_assignments 透過 devices.id 和 devices.owner_id 建立設備歸屬快照。

拆庫後銜接方案：
- devices.id 改為 machines.id 時，device_assignments 的 device_id 語義需重新定義
- machines 表無 owner_id（只有 machine_owner_id），SignalHub 授權查詢需改欄位名
- 建議：device_assignments 增加 machine_id 欄位，過渡期雙存 device_id / machine_id

---

## 四、stores 表需求評估

TODO.md 規劃 stores（場地/店面）。現行 iotv9 已有 venues 表。

若需另建 stores，建議 DDL：

    CREATE TABLE stores (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      venue_id BIGINT UNSIGNED NULL COMMENT '對應 iotv9.venues.id（過渡期）',
      owner_id BIGINT UNSIGNED NOT NULL,
      name VARCHAR(128) NOT NULL,
      address VARCHAR(255) NULL,
      city VARCHAR(64) NULL,
      timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Taipei',
      status ENUM('active','inactive') NOT NULL DEFAULT 'active',
      created_at TIMESTAMP NULL,
      updated_at TIMESTAMP NULL,
      KEY idx_owner_id (owner_id),
      KEY idx_venue_id (venue_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

注意：若 venues 已滿足需求，直接加欄位優於新建 stores，避免雙表維護。

---

## 五、無損遷移路徑評估

方案 A（View / Trigger 雙向鏡像）：
- 優點：舊 API 零改動
- 缺點：View 效能差；跨庫 Trigger MySQL 不支援；維護地獄
- 結論：不推薦

方案 B（應用層雙寫，Dual-write）：
- 優點：listener.py 已在做此事；可漸進切換，回滾容易
- 缺點：需保持兩表一致性，有短暫 race condition 視窗
- 結論：當前過渡期最安全，已部分實施

方案 C（階段性路由切換）：推薦
- Phase 2.1：補齊 machines 欄位
- Phase 2.2：背景同步腳本 devices -> machines
- Phase 2.3：讀切換（優先讀 machines）
- Phase 2.4：寫切換（Alliance、Owner 切換目標表）
- Phase 2.5：devices 唯讀封存
- 優點：每個 Phase 可獨立驗證回滾；無停機，投幣開分洗分全程不中斷

---

## 六、軟性欠費技術可行性

高頻事件（100ms 級別）下，profit_sharing_service 每次查 DB 無快取，MySQL 連線池有壓力。

Redis 快取設計：
    key：v9:profit_ratio:{device_id}  TTL=300s
    失效：Owner 更新分潤協議時主動 DEL
    淘汰策略：allkeys-lru

軟性欠費：
    key：v9:device:arrears:{chip_id}  TTL=3600
    listener.py 讀取後仍放行事件（軟性放行鐵律）
    同時非同步寫 machine_transactions（分潤固化）
    Owner Cron Job 每日累加 outstanding_amount

延遲估算：
- Redis 命中：< 1ms，可承受 100ms 頻率
- Cache Miss 首次 DB 查詢：< 10ms，可接受
- machine_transactions 寫入：建議非同步佇列化，避免阻塞 MQTT callback

---

## 七、風險矩陣

| 等級 | 風險 | 影響 | 機率 | 防禦機制 |
|------|------|------|------|---------|
| 高 | devices / machines 雙表資料不一致 | 分潤計算錯誤 | 高 | chip_id 唯一鍵；寫入加行鎖 |
| 高 | Alliance 同步欄位不完整 | 新出貨設備狀態異常 | 高 | Phase 2.1 先補齊 machines 欄位再切換 |
| 中 | device_assignments device_id 語義斷裂 | 設備歸屬查詢失效 | 中 | 過渡期增 machine_id；雙 FK 邏輯 |
| 中 | profit_sharing 無快取 DB 過載 | MySQL 連線池耗盡 | 中 | Redis 快取 TTL=300s |
| 低 | machines 缺 collector_owner_id | 硬件產權欄位遺失 | 低 | Phase 2.1 補欄位 |

---

## 八、分階段實施建議（工期）

    Phase 2.1（1-2天，需 HQ 送審）：補齊 machines 欄位
      ALTER TABLE machines ADD COLUMN collector_owner_id BIGINT UNSIGNED NULL
      ALTER TABLE machines ADD COLUMN venue_id BIGINT UNSIGNED NULL
      ALTER TABLE machines ADD COLUMN public_token VARCHAR(64) UNIQUE NULL
      ALTER TABLE machines ADD COLUMN machine_number VARCHAR(64) NULL
      ALTER TABLE machines ADD COLUMN machine_name VARCHAR(128) NULL

    Phase 2.2（2-3天）：背景資料同步
      backfill 腳本：以 chip_id 對齊 devices -> machines
      校驗腳本：比對兩表筆數與關鍵欄位

    Phase 2.3（1天）：讀切換
      credit-relay：優先讀 machines，fallback devices
      profit_sharing_service：讀 machines 分潤欄位
      加 Redis 分潤快取

    Phase 2.4（2-3天）：寫切換
      Alliance 出貨同步目標改 machines（協調 Allie）
      SignalHub device_assignments machine_id 欄位啟用
      Owner Device Model 切換至 machines 表

    Phase 2.5（N+30天）：devices 封存
      Trigger 攔截寫入 + 告警
      12 個月後歸檔至 archive_devices

物理分庫（新建 waw_infra 庫）建議在 Phase 2.3 讀切換驗證穩定後再執行。

---

## 九、結論

1. machines / machine_deployments / machine_transactions 三表已存在於 iotv9，Phase 2 核心工作是「補欄位 + 分庫」，不是重新建表。
2. 雙寫過渡已部分實施（listener.py），架構方向正確，需補齊剩餘服務。
3. 最高優先：Phase 2.1 補 machines 欄位（collector_owner_id、venue_id），避免 Alliance 出貨資料不完整。
4. 禁止：未完成欄位補齊前，不可切換 Alliance 寫入目標為 machines。
5. 建議：物理分庫在 Phase 2.3 讀切換驗證穩定後再執行。
6. 需 HQ 釐清：Alliance 出貨同步機制（HTTP API 橋接 vs 直接跨庫 SQL），影響 Phase 2.4 改動幅度。

---

**回報者**：Ina (Infra Master)
**回報時間**：2026-09-16 21:30
