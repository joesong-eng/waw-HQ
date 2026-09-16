# 任務回報：TASK_20260908_INA_DEVICES_SYNC_SCHEMA_AUDIT

**完成時間**：2026-09-08 16:25  
**執行者**：Ina (Infra Database Lead)

---

## 📋 審核結論與 devices 入庫白名單標準

### 一、Schema 審核結果

已完成對 `iotv9.devices` 表的完整審核，確認以下關鍵資訊：

#### 1.1 必填欄位（NOT NULL 且無 DEFAULT）
- `chip_id` (varchar(50), UNIQUE) — **物理唯一識別碼**
- `owner_id` (bigint unsigned) — **設備擁有者（MO）**

#### 1.2 WAW 2.0 雙產權欄位
- `collector_owner_id` (bigint unsigned, NULL) — **採集卡產權人**
- `machine_owner_id` (bigint unsigned, NULL) — **機台產權人**

**填寫原則**：Alliance 出貨時，兩欄位皆填入該訂單的 `owner_id`（業主）。

#### 1.3 狀態欄位確認
`status` 欄位為 ENUM，支援以下值：
- `pending_setup` ✅ **（預設值，SignalHub 設置精靈關鍵狀態）**
- `active`
- `maintenance`
- `lost`

#### 1.4 chip_id 唯一性約束
- 已確認 `UNIQUE KEY devices_chip_id_unique (chip_id)`
- Alliance 必須使用 `updateOrInsert(['chip_id' => $chipId], [...data])` 避免重複寫入

---

### 二、Alliance 跨庫寫入白名單（OrderController::ship）

#### ✅ 允許寫入的欄位清單

| 欄位名稱 | 型態 | 必填 | 預設值 | 說明 |
|---------|------|------|--------|------|
| `chip_id` | varchar(50) | ✅ YES | — | ESP32 MAC 或 SN，**UNIQUE 唯一識別** |
| `owner_id` | bigint unsigned | ✅ YES | — | 訂單業主 ID (FK -> users.id) |
| `collector_owner_id` | bigint unsigned | ⚠️ 建議填 | NULL | WAW 2.0 採集卡產權人（填入 owner_id） |
| `machine_owner_id` | bigint unsigned | ⚠️ 建議填 | NULL | WAW 2.0 機台產權人（填入 owner_id） |
| `name` | varchar(100) | ❌ NO | NULL | 設備別名（可選，建議 "ESP32-{chip_id 後4碼}"） |
| `type` | ENUM | ❌ NO | NULL | 機台類型（出貨時通常為 NULL，由 SignalHub 後續設定） |
| `status` | ENUM | ❌ NO | `pending_setup` | **出貨時必須寫入 'pending_setup'** |
| `subscription_status` | ENUM | ❌ NO | `expired` | 訂閱狀態（出貨時保持預設 'expired'） |
| `created_at` | timestamp | ❌ NO | NULL | Laravel 自動填入（建議由 Laravel 管理） |
| `updated_at` | timestamp | ❌ NO | NULL | Laravel 自動填入（建議由 Laravel 管理） |

#### 🚫 嚴禁寫入的欄位（歷史錯誤遺留）

- ❌ `mac_address` — **此欄位已不存在於 devices 表**
- ❌ `node_id` — **此欄位已不存在於 devices 表**
- ❌ `venue_id` — 出貨階段尚未分配場地，必須為 NULL
- ❌ `lifetime_*` 系列 — 運營數據，由即時事件更新
- ❌ `is_online`, `last_seen_at` — 由心跳機制更新
- ❌ 任何分成相關欄位 (`share_*`, `promo_*`) — 由 SignalHub 設置精靈配置

---

### 三、標準寫入範例（Alliance Laravel Code）

```php
// OrderController::ship 跨庫寫入範例
use Illuminate\Support\Facades\DB;

$wawCore = DB::connection('waw_core'); // config/database.php 中的 iotv9 連線

$wawCore->table('devices')->updateOrInsert(
    ['chip_id' => $chipId],  // 唯一鍵，避免重複
    [
        'owner_id'            => $order->owner_id,
        'collector_owner_id'  => $order->owner_id,  // WAW 2.0 雙產權
        'machine_owner_id'    => $order->owner_id,  // WAW 2.0 雙產權
        'name'                => "ESP32-" . substr($chipId, -4),  // 可選別名
        'type'                => null,  // 由 SignalHub 後續設定
        'status'              => 'pending_setup',  // ✅ 關鍵狀態
        'subscription_status' => 'expired',  // 預設無訂閱
        'created_at'          => now(),
        'updated_at'          => now(),
    ]
);
```

---

### 四、資料完整性與外鍵保護

#### 4.1 外鍵約束（現有）
當前 `devices` 表**沒有顯式的 FOREIGN KEY 約束**，僅有索引：
- `KEY devices_owner_id_index (owner_id)`
- `KEY devices_venue_id_index (venue_id)`
- `KEY idx_devices_collector_owner (collector_owner_id)`
- `KEY idx_devices_machine_owner (machine_owner_id)`

#### 4.2 應用層防護要求
Alliance 寫入前必須確保：
1. `owner_id` 存在於 `users` 表且 `role='machine_owner'`
2. `chip_id` 格式符合規範（ESP32 MAC 格式：`XX:XX:XX:XX:XX:XX` 或自訂 SN）
3. 使用 `updateOrInsert` 避免重複寫入導致 UNIQUE 衝突

---

### 五、與 Commit 672892c 歷史錯誤的對比

#### 錯誤案例（歷史 Commit）
```php
// ❌ 錯誤：寫入不存在的欄位
DB::connection('waw_core')->table('devices')->insert([
    'mac_address' => $chipId,  // ❌ 欄位不存在
    'node_id'     => $nodeId,  // ❌ 欄位不存在
    // ...
]);
```

**錯誤原因**：
- `devices` 表中無 `mac_address` 和 `node_id` 欄位
- 應使用 `chip_id` 作為物理唯一識別

#### ✅ 正確做法
參照上方「三、標準寫入範例」。

---

## 結論

✅ **審核完成，已發布 devices 入庫白名單規範**

### 核心要點總結
1. **必填欄位**：`chip_id`（UNIQUE）、`owner_id`
2. **WAW 2.0 雙產權**：`collector_owner_id` 和 `machine_owner_id` 皆填入 `owner_id`
3. **關鍵狀態**：`status = 'pending_setup'`（觸發 SignalHub 設置精靈）
4. **嚴禁欄位**：`mac_address`、`node_id`（已不存在）、`venue_id`（出貨時為 NULL）
5. **寫入方式**：使用 `updateOrInsert(['chip_id' => $chipId], [...])` 避免重複

### 後續協同
- **Allie (Alliance Lead)**：依此規範實作 `OrderController::ship` 跨庫寫入邏輯
- **Sidney (SignalHub Lead)**：確認 `status='pending_setup'` 可觸發設置精靈
- **Sophie (Owner Lead)**：確認訂閱系統與 `subscription_status` 欄位的整合

---

**審核者**：Ina (Infra Database Lead)  
**審核時間**：2026-09-08 16:25  
**任務狀態**：✅ 已完成
